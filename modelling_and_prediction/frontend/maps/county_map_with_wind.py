import pandas as pd
import geopandas as gpd
from shapely import wkt
from shapely.geometry import Point, Polygon
import folium
import math
import json
import numpy as np
import sys
from pathlib import Path

# ---------------------------------------------------------
# CONSTANTS
# ---------------------------------------------------------
CRS_WGS84 = "EPSG:4326"
CRS_ALBERS = "EPSG:5070"  # Albers Equal Area Conic (for USA)

# File paths
COUNTIES_FILE = "modelling_and_prediction/data/processed/US_COUNTIES.csv"
POPULATION_FILE = "modelling_and_prediction/data/processed/county_population_2023.csv"
OUTPUT_FILE = "modelling_and_prediction/frontend/maps/map_pop.html"

# Territories to exclude
TERRITORIES_TO_REMOVE = [
    "American Samoa",
    "Commonwealth Of The Northern Mariana Islands",
    "Guam",
    "Puerto Rico",
    "U.S. Virgin Islands",
    "Hawaii",
]

# Ellipse parameters
ELLIPSE_NUM_POINTS = 64
ELLIPSE_SHIFT_FACTOR = 0.25  # Shift 25% of base radius in wind direction
ELLIPSE_LATERAL_FACTOR = 0.9  # Slightly narrower perpendicular to wind

# Wind animation parameters
WIND_GRID_SIZE = 30
WIND_GRID_SPAN = 10
PARTICLE_COUNT = 1400  # Moderate number of arrows
PARTICLE_MAX_AGE = 120


# ---------------------------------------------------------
# 1. LOAD COUNTY POLYGONS
# ---------------------------------------------------------
def load_county_data(counties_file: str, population_file: str) -> gpd.GeoDataFrame:
    """
    Load county polygons and population data.
    
    Args:
        counties_file: Path to counties CSV file
        population_file: Path to population CSV file
        
    Returns:
        GeoDataFrame with counties and population
        
    Raises:
        FileNotFoundError: If files not found
        ValueError: If data cannot be processed
    """
    if not Path(counties_file).exists():
        raise FileNotFoundError(f"Counties file not found: {counties_file}")
    if not Path(population_file).exists():
        raise FileNotFoundError(f"Population file not found: {population_file}")
    
    try:
        counties = pd.read_csv(counties_file)
    except Exception as e:
        raise ValueError(f"Error loading counties file: {e}")
    
    try:
        counties["geometry"] = counties["BORDERS"].apply(wkt.loads)
    except Exception as e:
        raise ValueError(f"Error parsing geometries: {e}")
    
    gdf = gpd.GeoDataFrame(counties, geometry="geometry", crs=CRS_WGS84)
    
    # Remove territories
    gdf = gdf[~gdf["STATE"].isin(TERRITORIES_TO_REMOVE)]
    gdf["GEOID"] = gdf["GEOID"].astype(str).str.zfill(5)
    
    # Load population
    try:
        pop = pd.read_csv(population_file)
    except Exception as e:
        raise ValueError(f"Error loading population file: {e}")
    
    pop = pop.rename(columns={"POP_ESTIMATE_2023": "population"})
    pop["GEOID"] = pop["GEOID"].astype(str).str.zfill(5)
    
    gdf = gdf.merge(pop[["GEOID", "population"]], on="GEOID", how="left")
    gdf["population"] = gdf["population"].fillna(0)
    
    return gdf


# ---------------------------------------------------------
# 2. Color from heatmap value
# ---------------------------------------------------------
def color_from_heat(h: float) -> str:
    """
    Convert heat value (0-1) to RGB color.
    
    Args:
        h: Heat value between 0 and 1
        
    Returns:
        Hex color code (e.g. "#ff0000")
    """
    h = max(0, min(1, float(h)))
    r = 255
    g = int(255 * (1 - h))
    b = int(255 * (1 - h))
    return f"#{r:02x}{g:02x}{b:02x}"


# ---------------------------------------------------------
# 3. Generate wind field for canvas animation
# ---------------------------------------------------------
def generate_wind_field(speed_mph: float, direction_deg: float, 
                        center_lat: float, center_lon: float, 
                        size: int = WIND_GRID_SIZE, 
                        span: float = WIND_GRID_SPAN) -> tuple:
    """
    Generate wind field for canvas-based animation.
    
    Args:
        speed_mph: Wind speed in mph
        direction_deg: Wind direction in degrees (0° = North, 90° = East)
        center_lat: Center latitude
        center_lon: Center longitude
        size: Grid size
        span: Geographic extent of grid
        
    Returns:
        Tuple (u, v, lat, lon) - Wind components and grid coordinates
    """
    rad = math.radians(direction_deg)

    # Meteorological: Wind comes FROM direction_deg
    u_base = -speed_mph * math.sin(rad)
    v_base = -speed_mph * math.cos(rad)

    lat = [center_lat + span * (i - size/2) / size for i in range(size)]
    lon = [center_lon + span * (j - size/2) / size for j in range(size)]

    u = [[u_base for _ in range(size)] for _ in range(size)]
    v = [[v_base for _ in range(size)] for _ in range(size)]

    return u, v, lat, lon


# ---------------------------------------------------------
# 4. Create ellipse (for fire spread based on wind)
# ---------------------------------------------------------
def create_wind_ellipse(lat: float, lon: float, radius_km: float, 
                        wind_speed_mph: float, wind_direction_deg: float) -> Polygon:
    """
    Create an ellipse for fire spread based on wind.
    
    LOGIC:
    1. Base is a circle with radius_km
    2. Ellipse is stretched in wind direction (where wind blows TO)
    3. Center is shifted slightly downwind
    
    East wind (90°): Wind blows westward → Ellipse points west (left)
    North wind (0°): Wind blows southward → Ellipse points south (down)
    """
    # Project for precise calculation
    point = Point(lon, lat)
    gdf_point = gpd.GeoDataFrame([1], geometry=[point], crs=CRS_WGS84)
    gdf_proj = gdf_point.to_crs(CRS_ALBERS)
    center_x = gdf_proj.geometry.iloc[0].x
    center_y = gdf_proj.geometry.iloc[0].y
    
    # Base radius in meters
    radius_m = radius_km * 1000
    
    # Wind stretch: moderate, not extreme
    # At 0 mph: circle (1.0x)
    # At 30 mph: 1.3x stretch
    # At 60 mph: 1.6x stretch  
    stretch_factor = 1.0 + (wind_speed_mph / 100.0)
    
    # Wind direction: WHERE wind blows TO (= fire spread direction)
    # wind_direction_deg = where wind comes FROM (meteorological convention)
    # wind_to_deg = where wind blows TO = wind_direction_deg + 180°
    wind_to_deg = (wind_direction_deg + 180) % 360
    wind_to_rad = math.radians(wind_to_deg)
    
    # In EPSG:5070 (and most projections):
    # - X-axis = East (+X = right)
    # - Y-axis = North (+Y = up)
    #
    # For GEOGRAPHIC angles (0°=N, 90°=E, 180°=S, 270°=W):
    # - dx = sin(geo_angle)  → East-West component
    # - dy = cos(geo_angle)  → North-South component
    #
    # Examples:
    # - 270° (West): sin(270°)=-1, cos(270°)=0 → left ✓
    # - 180° (South): sin(180°)=0, cos(180°)=-1 → down ✓
    # - 90° (East): sin(90°)=1, cos(90°)=0 → right ✓
    # - 0° (North): sin(0°)=0, cos(0°)=1 → up ✓
    dx = math.sin(wind_to_rad)  # East-West component
    dy = math.cos(wind_to_rad)  # North-South component
    
    # Create ellipse:
    # - Major axis (a) = radius * stretch_factor, points in wind direction
    # - Minor axis (b) = radius, perpendicular to wind
    a = radius_m * stretch_factor  # Major axis (in wind direction)
    b = radius_m                    # Minor axis (normal radius)
    
    # Shift: Fire origin should be at the BACK edge of ellipse
    shift_to_wind = (a - b) * 0.5
    ellipse_center_x = center_x + shift_to_wind * dx
    ellipse_center_y = center_y + shift_to_wind * dy
    
    print(f"  Wind from {wind_direction_deg}° → blows to {wind_to_deg}°")
    print(f"  Direction: dx={dx:.2f}, dy={dy:.2f}")
    print(f"  Ellipse: a={a/1000:.1f}km, b={b/1000:.1f}km, shift={shift_to_wind/1000:.1f}km")
    
    ellipse_points = []
    for i in range(ELLIPSE_NUM_POINTS):
        t = 2 * math.pi * i / ELLIPSE_NUM_POINTS
        
        # Ellipse in local coordinates (major axis along X)
        x_local = a * math.cos(t)
        y_local = b * math.sin(t)
        
        # Rotation: Major axis should point in wind direction (dx, dy)
        # Rotation matrix transforms (1,0) to (dx, dy):
        # [dx  -dy]   
        # [dy   dx]   
        x_rot = x_local * dx - y_local * dy
        y_rot = x_local * dy + y_local * dx
        
        # Add to ellipse center
        x_final = ellipse_center_x + x_rot
        y_final = ellipse_center_y + y_rot
        
        ellipse_points.append((x_final, y_final))
    
    return Polygon(ellipse_points)


# ---------------------------------------------------------
# 5. Generate fire animation JavaScript 
# ---------------------------------------------------------
def generate_fire_animation_script(map_id: str, center_lat: float, center_lon: float,
                                    ellipse_coords: list, wind_direction_deg: float,
                                    animation_duration_sec: float = 15.0) -> str:
    """
    Generate JavaScript for REALISTIC animated fire spread.
    
    Features:
    - Perlin Noise for irregular, wavy edges
    - Holes and gaps in fire front
    - "Fingers" extending in wind direction
    - Asymmetric growth
    - Curly, distorted edges
    """
    safe_map_id = map_id.replace("'", "\\'").replace('"', '\\"')
    ellipse_json = json.dumps(ellipse_coords)
    
    return f"""
    <style>
        #fireControls {{
            position: absolute;
            bottom: 12px;
            right: 12px;
            z-index: 1001;
            background: rgba(255, 255, 255, 0.95);
            padding: 8px 12px;
            border-radius: 6px;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.12);
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            border: 1px solid #e0e0e0;
        }}
        #fireControls button {{
            background: #2c3e50;
            color: white;
            border: none;
            padding: 6px 12px;
            margin: 0 3px;
            border-radius: 4px;
            cursor: pointer;
            font-weight: 500;
            font-size: 11px;
            transition: background 0.2s, transform 0.15s;
        }}
        #fireControls button:hover {{
            background: #34495e;
        }}
        #fireControls button:disabled {{
            background: #95a5a6;
            cursor: not-allowed;
        }}
        #progressContainer {{
            margin-top: 6px;
            text-align: center;
        }}
        #progressBar {{
            width: 120px;
            height: 4px;
            background: #ecf0f1;
            border-radius: 2px;
            overflow: hidden;
            display: inline-block;
        }}
        #progressFill {{
            height: 100%;
            background: #3498db;
            width: 0%;
            transition: width 0.05s linear;
        }}
        #timeDisplay {{
            margin-left: 6px;
            font-size: 10px;
            color: #7f8c8d;
            font-weight: 500;
        }}
        #fireStatus {{
            display: none;
        }}
    </style>
    
    <div id="fireControls">
        <button id="startFireBtn">▶ Start</button>
        <button id="resetFireBtn">↺ Reset</button>
        <div id="progressContainer">
            <div id="progressBar"><div id="progressFill"></div></div>
            <span id="timeDisplay">0:00</span>
        </div>
        <div id="fireStatus"></div>
    </div>
    
    <script>
    (function() {{
        var fireAnimationId = null;
        var fireStartTime = null;
        var fireProgress = 0;
        var isFireRunning = false;
        var fireLayers = [];
        var noiseSeeds = [];
        var holeSectors = [];
        var fingerAngles = [];
        
        var ANIMATION_DURATION = {animation_duration_sec * 1000};
        var CENTER_LAT = {center_lat};
        var CENTER_LON = {center_lon};
        var FINAL_ELLIPSE = {ellipse_json};
        var WIND_DIR = {wind_direction_deg};
        
        // Simplex Noise Implementation (vereinfacht)
        var perm = new Array(512);
        var gradP = new Array(512);
        var grad3 = [
            [1,1,0],[-1,1,0],[1,-1,0],[-1,-1,0],
            [1,0,1],[-1,0,1],[1,0,-1],[-1,0,-1],
            [0,1,1],[0,-1,1],[0,1,-1],[0,-1,-1]
        ];
        
        function initNoise(seed) {{
            var p = [];
            for (var i = 0; i < 256; i++) p[i] = i;
            // Shuffle mit Seed
            var n, swap;
            for (var i = 255; i > 0; i--) {{
                n = Math.floor((seed = (seed * 16807) % 2147483647) / 2147483647 * (i + 1));
                swap = p[i]; p[i] = p[n]; p[n] = swap;
            }}
            for (var i = 0; i < 512; i++) {{
                perm[i] = p[i & 255];
                gradP[i] = grad3[perm[i] % 12];
            }}
        }}
        
        function dot2(g, x, y) {{ return g[0]*x + g[1]*y; }}
        
        function noise2D(x, y) {{
            var F2 = 0.5 * (Math.sqrt(3) - 1);
            var G2 = (3 - Math.sqrt(3)) / 6;
            var s = (x + y) * F2;
            var i = Math.floor(x + s);
            var j = Math.floor(y + s);
            var t = (i + j) * G2;
            var X0 = i - t, Y0 = j - t;
            var x0 = x - X0, y0 = y - Y0;
            var i1, j1;
            if (x0 > y0) {{ i1 = 1; j1 = 0; }} else {{ i1 = 0; j1 = 1; }}
            var x1 = x0 - i1 + G2, y1 = y0 - j1 + G2;
            var x2 = x0 - 1 + 2*G2, y2 = y0 - 1 + 2*G2;
            i &= 255; j &= 255;
            var gi0 = gradP[i + perm[j]];
            var gi1 = gradP[i + i1 + perm[j + j1]];
            var gi2 = gradP[i + 1 + perm[j + 1]];
            var t0 = 0.5 - x0*x0 - y0*y0;
            var n0 = t0 < 0 ? 0 : Math.pow(t0, 4) * dot2(gi0, x0, y0);
            var t1 = 0.5 - x1*x1 - y1*y1;
            var n1 = t1 < 0 ? 0 : Math.pow(t1, 4) * dot2(gi1, x1, y1);
            var t2 = 0.5 - x2*x2 - y2*y2;
            var n2 = t2 < 0 ? 0 : Math.pow(t2, 4) * dot2(gi2, x2, y2);
            return 70 * (n0 + n1 + n2);
        }}
        
        // Multi-octave noise for more complex patterns
        function fbm(x, y, octaves, persistence) {{
            var total = 0, frequency = 1, amplitude = 1, maxValue = 0;
            for (var i = 0; i < octaves; i++) {{
                total += noise2D(x * frequency, y * frequency) * amplitude;
                maxValue += amplitude;
                amplitude *= persistence;
                frequency *= 2;
            }}
            return total / maxValue;
        }}
        
        function initFireParams() {{
            // Random seed for this animation
            var seed = Math.floor(Math.random() * 1000000);
            initNoise(seed);
            
            // Generate small indentations (3-5 pieces)
            holeSectors = [];
            var numHoles = 3 + Math.floor(Math.random() * 3);
            for (var i = 0; i < numHoles; i++) {{
                holeSectors.push({{
                    angle: Math.random() * Math.PI * 2,
                    width: 0.15 + Math.random() * 0.1,
                    depth: 0.15 + Math.random() * 0.1,  // Very shallow
                    startProgress: 0.1 + Math.random() * 0.15,
                    fillRate: 1.2 + Math.random() * 0.5  // Fill very fast
                }});
            }}
            
            // Generate small protrusions in wind direction (4-6 pieces)
            fingerAngles = [];
            var windToRad = (WIND_DIR + 180) * Math.PI / 180;
            var numFingers = 4 + Math.floor(Math.random() * 3);
            for (var i = 0; i < numFingers; i++) {{
                var spreadAngle = (Math.random() - 0.5) * Math.PI * 0.6;
                fingerAngles.push({{
                    angle: windToRad + spreadAngle,
                    length: 0.04 + Math.random() * 0.06,  // Very short
                    width: 0.12 + Math.random() * 0.08,
                    speed: 1.2 + Math.random() * 0.3
                }});
            }}
        }}
        
        function initFireAnimation() {{
            if (typeof L === 'undefined') {{
                setTimeout(initFireAnimation, 100);
                return;
            }}
            
            var map = window.map || {safe_map_id};
            if (!map || typeof map.getBounds !== 'function') {{
                setTimeout(initFireAnimation, 100);
                return;
            }}
            
            document.getElementById('startFireBtn').addEventListener('click', function() {{
                if (!isFireRunning) startFire(map);
            }});
            
            document.getElementById('resetFireBtn').addEventListener('click', function() {{
                resetFire(map);
            }});
            
            console.log('Realistic fire animation initialized!');
        }}
        
        function startFire(map) {{
            isFireRunning = true;
            fireStartTime = Date.now();
            fireProgress = 0;
            initFireParams();
            
            document.getElementById('startFireBtn').textContent = 'Running...';
            document.getElementById('startFireBtn').disabled = true;
            document.getElementById('fireStatus').textContent = 'Simulating fire spread...';
            
            animateFire(map);
        }}
        
        function resetFire(map) {{
            isFireRunning = false;
            fireProgress = 0;
            
            if (fireAnimationId) {{
                cancelAnimationFrame(fireAnimationId);
                fireAnimationId = null;
            }}
            
            fireLayers.forEach(function(layer) {{
                if (layer) map.removeLayer(layer);
            }});
            fireLayers = [];
            
            document.getElementById('startFireBtn').textContent = 'Start Simulation';
            document.getElementById('startFireBtn').disabled = false;
            document.getElementById('progressFill').style.width = '0%';
            document.getElementById('timeDisplay').textContent = '0:00';
            document.getElementById('fireStatus').textContent = 'Ready';
        }}
        
        function getRealisticFireShape(progress, time) {{
            var coords = [];
            var windToRad = (WIND_DIR + 180) * Math.PI / 180;
            var windDx = Math.sin(windToRad);
            var windDy = Math.cos(windToRad);
            
            // Points for edges
            var numPoints = 80;
            
            // === SMOOTHING FACTOR ===
            // At start (progress=0): full effects
            // At end (progress=1): smooth ellipse
            // Effects fade in last 30%
            var chaosAmount = progress < 0.7 ? 1.0 : Math.max(0, (1 - progress) / 0.3);
            chaosAmount = Math.pow(chaosAmount, 1.5);  // Smoother transition
            
            for (var i = 0; i < numPoints; i++) {{
                var angle = (i / numPoints) * Math.PI * 2;
                
                // Find corresponding point in final ellipse
                var ellipseIdx = Math.floor((i / numPoints) * FINAL_ELLIPSE.length);
                var finalPoint = FINAL_ELLIPSE[ellipseIdx % FINAL_ELLIPSE.length];
                var dx = finalPoint[1] - CENTER_LON;
                var dy = finalPoint[0] - CENTER_LAT;
                
                // Wind asymmetry (faster in wind direction) - always active
                var angleDiff = angle - windToRad;
                var windFactor = 0.5 + 0.5 * (0.5 + 0.5 * Math.cos(angleDiff));
                
                // Base progress
                var easedProgress = 1 - Math.pow(1 - progress, 2);
                var localProgress = easedProgress * windFactor;
                
                // === SOFT WAVES - CLOSE TO ELLIPSE ===
                var noiseScale = 1.5;
                var noiseX = Math.cos(angle) * noiseScale + time * 0.1;
                var noiseY = Math.sin(angle) * noiseScale + time * 0.08;
                var edgeNoise = fbm(noiseX, noiseY, 2, 0.5);
                // Very small amplitude - stays close to ellipse
                var noiseEffect = edgeNoise * 0.06 * chaosAmount;
                localProgress *= (0.98 + noiseEffect);
                
                // === SMALL INDENTATIONS (not holes, just slight dents) ===
                if (chaosAmount > 0.1) {{
                    for (var h = 0; h < holeSectors.length; h++) {{
                        var hole = holeSectors[h];
                        var holeAngleDiff = Math.abs(angle - hole.angle);
                        if (holeAngleDiff > Math.PI) holeAngleDiff = Math.PI * 2 - holeAngleDiff;
                        
                        if (holeAngleDiff < hole.width && progress > hole.startProgress) {{
                            var holeStrength = 1 - (holeAngleDiff / hole.width);
                            holeStrength = Math.pow(holeStrength, 2);
                            var holeFill = Math.min(1, (progress - hole.startProgress) * hole.fillRate * 2);
                            // Very shallow dents - max 8% depth
                            var holeDepth = hole.depth * 0.2 * (1 - holeFill) * holeStrength * chaosAmount;
                            localProgress *= (1 - holeDepth);
                        }}
                    }}
                }}
                
                // === SMALL PROTRUSIONS in wind direction ===
                if (chaosAmount > 0.1) {{
                    for (var f = 0; f < fingerAngles.length; f++) {{
                        var finger = fingerAngles[f];
                        var fingerAngleDiff = Math.abs(angle - finger.angle);
                        if (fingerAngleDiff > Math.PI) fingerAngleDiff = Math.PI * 2 - fingerAngleDiff;
                        
                        if (fingerAngleDiff < finger.width) {{
                            var fingerStrength = 1 - (fingerAngleDiff / finger.width);
                            fingerStrength = Math.pow(fingerStrength, 2);
                            var fingerProgress = Math.min(progress * finger.speed, 1);
                            // Very short protrusions - max 5% beyond ellipse
                            var fingerEffect = finger.length * 0.25 * fingerStrength * fingerProgress * chaosAmount;
                            localProgress += fingerEffect;
                        }}
                    }}
                }}
                
                // === Micro-Variation (kaum sichtbar) ===
                var microNoise = noise2D(angle * 6, time * 0.3);
                var microEffect = microNoise * 0.015 * chaosAmount;
                localProgress *= (1 + microEffect);
                
                // Final position
                localProgress = Math.max(0.02, Math.min(1.05, localProgress));
                
                // === SMOOTH TRANSITION TO ELLIPSE ===
                // Continuous smoothing - starts early, ends soft
                
                var targetProgress = easedProgress;  // Target: exact ellipse
                var deviation = Math.abs(localProgress - targetProgress);
                
                // From 50% progress, start soft smoothing
                if (progress > 0.5) {{
                    // Smooth factor: 0 at 50%, 1 at 100%
                    var smoothFactor = (progress - 0.5) / 0.5;
                    // Cubic easing for extra-smooth transition
                    smoothFactor = smoothFactor * smoothFactor * (3 - 2 * smoothFactor);
                    
                    // Points close to ellipse smooth faster
                    var proximityBonus = 1 - Math.min(deviation * 5, 0.5);
                    var blendAmount = smoothFactor * (0.6 + proximityBonus * 0.4);
                    blendAmount = Math.min(1, blendAmount);
                    
                    // Soft interpolation
                    localProgress = localProgress + (targetProgress - localProgress) * blendAmount;
                }}
                
                // Last 8%: Final smooth to perfect ellipse
                if (progress > 0.92) {{
                    var finalSmooth = (progress - 0.92) / 0.08;
                    finalSmooth = finalSmooth * finalSmooth;
                    localProgress = localProgress + (targetProgress - localProgress) * finalSmooth;
                }}
                
                var newLat = CENTER_LAT + dy * localProgress;
                var newLon = CENTER_LON + dx * localProgress;
                
                coords.push([newLat, newLon]);
            }}
            
            return coords;
        }}
        
        function animateFire(map) {{
            var elapsed = Date.now() - fireStartTime;
            fireProgress = Math.min(1, elapsed / ANIMATION_DURATION);
            var time = elapsed / 1000;
            
            // Update Progress Bar
            document.getElementById('progressFill').style.width = (fireProgress * 100) + '%';
            var seconds = Math.floor(elapsed / 1000);
            var ms = Math.floor((elapsed % 1000) / 10);
            document.getElementById('timeDisplay').textContent = seconds + ':' + (ms < 10 ? '0' : '') + ms;
            
            // Status Update
            var percent = Math.floor(fireProgress * 100);
            document.getElementById('fireStatus').textContent = 'Progress: ' + percent + '%';
            
            // Remove old fire layers
            fireLayers.forEach(function(layer) {{
                if (layer) map.removeLayer(layer);
            }});
            fireLayers = [];
            
            // Calculate realistic fire shape
            var currentCoords = getRealisticFireShape(fireProgress, time);
            
            // === MULTIPLE LAYERS for more realistic look ===
            
            // Äußerer Glühring (schwach)
            if (fireProgress > 0.1) {{
                var outerGlow = L.polygon(currentCoords, {{
                    color: 'rgba(255, 100, 0, 0.3)',
                    fillColor: 'rgba(255, 150, 50, 0.1)',
                    fillOpacity: 0.1,
                    weight: 8,
                    lineCap: 'round',
                    lineJoin: 'round'
                }}).addTo(map);
                fireLayers.push(outerGlow);
            }}
            
            // Hauptfeuer (rot-orange, ohne gelben Kern)
            var mainR = 255;
            var mainG = Math.floor(60 + fireProgress * 70);
            var mainB = 0;
            var mainFire = L.polygon(currentCoords, {{
                color: 'rgb(' + mainR + ',' + Math.floor(mainG * 0.5) + ',0)',
                fillColor: 'rgb(' + mainR + ',' + mainG + ',' + mainB + ')',
                fillOpacity: 0.4 + fireProgress * 0.1,
                weight: 3,
                lineCap: 'round',
                lineJoin: 'round'
            }}).addTo(map);
            fireLayers.push(mainFire);
            
            // Animation fortsetzen oder beenden
            if (fireProgress < 1) {{
                fireAnimationId = requestAnimationFrame(function() {{
                    animateFire(map);
                }});
            }} else {{
                isFireRunning = false;
                document.getElementById('startFireBtn').textContent = 'Complete';
                document.getElementById('fireStatus').textContent = 'Simulation complete';
                
                setTimeout(function() {{
                    document.getElementById('startFireBtn').textContent = 'Run Again';
                    document.getElementById('startFireBtn').disabled = false;
                }}, 2000);
            }}
        }}
        
        function waitForMap() {{
            var map = window.map || {safe_map_id};
            if (map && typeof map.whenReady === 'function') {{
                map.whenReady(initFireAnimation);
            }} else if (map && typeof map.getBounds === 'function') {{
                initFireAnimation();
            }} else {{
                setTimeout(waitForMap, 100);
            }}
        }}
        
        waitForMap();
    }})();
    </script>
    """


# ---------------------------------------------------------
# 6. Generate JavaScript for wind animation
# ---------------------------------------------------------
def generate_wind_script(map_id: str, u_json: str, v_json: str, 
                         lat_json: str, lon_json: str, 
                         wind_direction_deg: float) -> str:
    """
    Generate JavaScript for wind animation.
    
    Args:
        map_id: Leaflet map ID
        u_json: JSON string of U components
        v_json: JSON string of V components
        lat_json: JSON string of latitudes
        lon_json: JSON string of longitudes
        wind_direction_deg: Wind direction in degrees
        
    Returns:
        HTML/JavaScript string for wind animation
    """
    # Escape map_id for JavaScript safety
    safe_map_id = map_id.replace("'", "\\'").replace('"', '\\"')
    
    return f"""
    <style>
        #windCanvas {{
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            pointer-events: none;
            z-index: 1000;
        }}
    </style>
    <canvas id="windCanvas"></canvas>
    <script>
    (function() {{
        var animationId = null;
        
        function initWindAnimation() {{
            if (typeof L === 'undefined') {{
                setTimeout(initWindAnimation, 100);
                return;
            }}
            
            var map = window.map || {safe_map_id};
            if (!map || typeof map.getBounds !== 'function') {{
                setTimeout(initWindAnimation, 100);
                return;
            }}
            
            var canvas = document.getElementById('windCanvas');
            if (!canvas) {{
                setTimeout(initWindAnimation, 100);
                return;
            }}
            
            var ctx = canvas.getContext('2d');
            var particles = [];
            
            // Wind-Daten
            var u = {u_json};
            var v = {v_json};
            var latGrid = {lat_json};
            var lonGrid = {lon_json};
            
            // Canvas-Größe anpassen
            function resizeCanvas() {{
                var mapElement = document.getElementById('{safe_map_id}');
                if (mapElement) {{
                    var rect = mapElement.getBoundingClientRect();
                    canvas.width = rect.width;
                    canvas.height = rect.height;
                    canvas.style.width = rect.width + 'px';
                    canvas.style.height = rect.height + 'px';
                }}
            }}
            
            resizeCanvas();
            map.on('resize', resizeCanvas);
            map.on('zoomend', resizeCanvas);
            map.on('moveend', resizeCanvas);
            
            // Cleanup bei Seitenwechsel
            window.addEventListener('beforeunload', function() {{
                if (animationId) {{
                    cancelAnimationFrame(animationId);
                    animationId = null;
                }}
            }});
            
            // Particle class
            function Particle() {{
                var bounds = map.getBounds();
                this.lat = bounds.getSouth() + Math.random() * (bounds.getNorth() - bounds.getSouth());
                this.lon = bounds.getWest() + Math.random() * (bounds.getEast() - bounds.getWest());
                this.age = Math.random() * 90;
                this.maxAge = {PARTICLE_MAX_AGE};
            }}
            
            // Bilinear interpolation for smoother wind data
            function getWindAt(lat, lon) {{
                var i0 = 0, i1 = 0, j0 = 0, j1 = 0;
                var found = false;
                
                for (var i = 0; i < latGrid.length - 1; i++) {{
                    if (lat >= latGrid[i] && lat <= latGrid[i + 1]) {{
                        i0 = i;
                        i1 = i + 1;
                        found = true;
                        break;
                    }}
                }}
                if (!found) {{
                    i0 = lat < latGrid[0] ? 0 : latGrid.length - 1;
                    i1 = i0;
                }}
                
                found = false;
                for (var j = 0; j < lonGrid.length - 1; j++) {{
                    if (lon >= lonGrid[j] && lon <= lonGrid[j + 1]) {{
                        j0 = j;
                        j1 = j + 1;
                        found = true;
                        break;
                    }}
                }}
                if (!found) {{
                    j0 = lon < lonGrid[0] ? 0 : lonGrid.length - 1;
                    j1 = j0;
                }}
                
                var lat0 = latGrid[i0], lat1 = latGrid[i1];
                var lon0 = lonGrid[j0], lon1 = lonGrid[j1];
                
                var fx = (lon - lon0) / (lon1 - lon0 || 1);
                var fy = (lat - lat0) / (lat1 - lat0 || 1);
                
                var u00 = u[i0][j0], u01 = u[i0][j1];
                var u10 = u[i1][j0], u11 = u[i1][j1];
                var v00 = v[i0][j0], v01 = v[i0][j1];
                var v10 = v[i1][j0], v11 = v[i1][j1];
                
                var u_interp = (1 - fx) * (1 - fy) * u00 + 
                              fx * (1 - fy) * u01 + 
                              (1 - fx) * fy * u10 + 
                              fx * fy * u11;
                              
                var v_interp = (1 - fx) * (1 - fy) * v00 + 
                              fx * (1 - fy) * v01 + 
                              (1 - fx) * fy * v10 + 
                              fx * fy * v11;
                
                return {{u: u_interp, v: v_interp}};
            }}
            
            // Draw arrow (points in wind direction)
            function drawArrow(ctx, x, y, angle, length, color, alpha) {{
                ctx.save();
                ctx.translate(x, y);
                ctx.rotate(angle);
                
                var arrowLength = Math.min(Math.max(length * 0.8, 8), 40);
                var arrowWidth = Math.max(arrowLength * 0.25, 3);
                
                ctx.fillStyle = 'rgba(' + color + ', ' + alpha + ')';
                ctx.strokeStyle = 'rgba(' + color + ', ' + (alpha * 0.8) + ')';
                ctx.lineWidth = 1.2;
                
                ctx.beginPath();
                ctx.moveTo(arrowLength, 0);
                ctx.lineTo(arrowLength - arrowWidth, -arrowWidth / 2);
                ctx.lineTo(arrowLength - arrowWidth, arrowWidth / 2);
                ctx.closePath();
                ctx.fill();
                
                ctx.beginPath();
                ctx.moveTo(0, 0);
                ctx.lineTo(arrowLength - arrowWidth, 0);
                ctx.stroke();
                
                ctx.restore();
            }}
            
            // Create particles (arrows)
            function createParticles() {{
                var bounds = map.getBounds();
                for (var i = 0; i < {PARTICLE_COUNT}; i++) {{
                    var p = new Particle();
                    p.lat = bounds.getSouth() + Math.random() * (bounds.getNorth() - bounds.getSouth());
                    p.lon = bounds.getWest() + Math.random() * (bounds.getEast() - bounds.getWest());
                    particles.push(p);
                }}
            }}
            
            // Animation loop - smooth movement
            function animate() {{
                ctx.clearRect(0, 0, canvas.width, canvas.height);
                
                var bounds = map.getBounds();
                var sw = bounds.getSouthWest();
                var ne = bounds.getNorthEast();
                
                particles.forEach(function(p) {{
                    var wind = getWindAt(p.lat, p.lon);
                    var speed = Math.sqrt(wind.u * wind.u + wind.v * wind.v);
                    
                    // Zoom-dependent speed
                    var zoom = map.getZoom();
                    var baseScale = 0.0001;
                    var zoomFactor = Math.pow(0.7, zoom - 7);
                    var scale = baseScale * zoomFactor;
                    
                    p.lat += wind.v * scale;
                    p.lon += wind.u * scale;
                    p.age += 0.3;
                    
                    var point = map.latLngToContainerPoint([p.lat, p.lon]);
                    
                    if (point.x < -100 || point.x > canvas.width + 100 || 
                        point.y < -100 || point.y > canvas.height + 100 ||
                        p.lat < sw.lat - 2 || p.lat > ne.lat + 2 ||
                        p.lon < sw.lng - 2 || p.lon > ne.lng + 2) {{
                        p.lat = sw.lat + Math.random() * (ne.lat - sw.lat);
                        p.lon = sw.lng + Math.random() * (ne.lng - sw.lng);
                        p.age = 0;
                        point = map.latLngToContainerPoint([p.lat, p.lon]);
                    }}
                    
                    // Calculate angle (arrow points IN wind direction)
                    var windDirectionDeg = {wind_direction_deg};
                    var arrowDirectionDeg = (windDirectionDeg + 180) % 360;
                    var angle = ((arrowDirectionDeg - 90) * Math.PI) / 180;
                    
                    // Color: Dark blue, very transparent
                    var normalizedSpeed = Math.min(speed / 50, 1);
                    // Dark blue gradient: medium blue to very dark blue
                    var r = Math.floor(20 + normalizedSpeed * 30);   // 20-50
                    var g = Math.floor(50 + normalizedSpeed * 80);  // 50-130
                    var b = Math.floor(100 + normalizedSpeed * 155); // 100-255
                    var color = r + ', ' + g + ', ' + b;
                    
                    var alpha = 0.25 + (Math.random() * 0.15);  // Much more transparent
                    
                    if (point.x >= -50 && point.x <= canvas.width + 50 &&
                        point.y >= -50 && point.y <= canvas.height + 50) {{
                        drawArrow(ctx, point.x, point.y, angle, speed * 0.7, color, alpha);
                    }}
                    
                    if (p.age > p.maxAge) {{
                        p.lat = sw.lat + Math.random() * (ne.lat - sw.lat);
                        p.lon = sw.lng + Math.random() * (ne.lng - sw.lng);
                        p.age = 0;
                    }}
                }});
                
                animationId = requestAnimationFrame(animate);
            }}
            
            createParticles();
            animate();
            
            console.log('Wind animation started!');
        }}
        
        function waitForMap() {{
            var map = window.map || {safe_map_id};
            if (map && typeof map.whenReady === 'function') {{
                map.whenReady(initWindAnimation);
            }} else if (map && typeof map.getBounds === 'function') {{
                initWindAnimation();
            }} else {{
                setTimeout(waitForMap, 100);
            }}
        }}
        
        waitForMap();
    }})();
    </script>
    """


# ---------------------------------------------------------
# 7. Main function
# ---------------------------------------------------------
def population_map(gdf: gpd.GeoDataFrame, lat: float, lon: float, 
                   radius_km: float, wind_speed_mph: float, 
                   wind_direction_deg: float) -> tuple:
    """
    Create a map with population data and wind animation.
    
    Args:
        gdf: GeoDataFrame with county data
        lat: Center latitude
        lon: Center longitude
        radius_km: Radius in kilometers
        wind_speed_mph: Wind speed in mph
        wind_direction_deg: Wind direction in degrees
        
    Returns:
        Tuple (total_pop, table_sorted, map, wind_data)
    """
    radius_m = radius_km * 1000

    # Project for precise area calculation
    gdf_proj = gdf.to_crs(CRS_ALBERS)
    
    # ELLIPSE instead of circle (based on wind)
    ellipse_proj_geom = create_wind_ellipse(lat, lon, radius_km, wind_speed_mph, wind_direction_deg)

    # Intersect counties with ELLIPSE (not circle!)
    intersects = gdf_proj[gdf_proj.intersects(ellipse_proj_geom)].copy()
    
    # Check if counties found
    if intersects.empty:
        print("Warning: No counties found in area.")
        total_pop = 0
        table_sorted = intersects.to_crs(CRS_WGS84)
    else:
        intersects["intersection_area"] = intersects.intersection(ellipse_proj_geom).area
        intersects["county_area"] = intersects.geometry.area
        
        # Prevent division by zero
        intersects["fraction"] = intersects.apply(
            lambda row: row["intersection_area"] / row["county_area"] 
            if row["county_area"] > 0 else 0, 
            axis=1
        )
        intersects["population_contrib"] = intersects["population"] * intersects["fraction"]

        total_pop = intersects["population_contrib"].sum()

        # Heat based on fraction (how much of county is affected)
        # fraction is already between 0 and 1, use directly as heat
        intersects["heat"] = intersects["fraction"].clip(0, 1)

        intersects = intersects.to_crs(CRS_WGS84)
        table_sorted = intersects.sort_values("population_contrib", ascending=False)

    # -------- MAP --------
    m = folium.Map(location=[lat, lon], zoom_start=7, tiles="CartoDB positron")
    
    # Map ID for JavaScript reference
    map_id = m.get_name()
    
    # Global reference for wind layer (set after map initialization)
    m.get_root().script.add_child(folium.Element(f"window.map = {map_id};"))
    
    # Prepare ellipse for animation (in WGS84)
    ellipse_wgs84 = gpd.GeoDataFrame([1], geometry=[ellipse_proj_geom], crs=CRS_ALBERS)
    ellipse_wgs84 = ellipse_wgs84.to_crs(CRS_WGS84)
    ellipse_geom_wgs84 = ellipse_wgs84.geometry.iloc[0]
    
    # Extract ellipse coordinates for animation
    ellipse_coords = list(ellipse_geom_wgs84.exterior.coords)
    # Format: [[lat, lon], [lat, lon], ...] for Leaflet
    ellipse_coords_latlon = [[coord[1], coord[0]] for coord in ellipse_coords]
    
    # Fire origin marker with fire icon
    folium.Marker(
        [lat, lon], 
        popup=f"🔥 Fire Origin<br>Radius: {radius_km} km<br>Wind: {wind_speed_mph} mph from {wind_direction_deg}°",
        icon=folium.Icon(color='red', icon='fire', prefix='fa')
    ).add_to(m)

    # Draw counties (only if present)
    if not table_sorted.empty:
        for _, row in table_sorted.iterrows():
            folium.GeoJson(
                row.geometry.__geo_interface__,
                style_function=lambda x, fc=color_from_heat(row["heat"]): {
                    "fillColor": fc,
                    "color": "black",
                    "weight": 1,
                    "fillOpacity": 0.55,
                },
                tooltip=folium.Tooltip(
                    f"{row['COUNTY']}, {row['STATE']}<br>"
                    f"Population: {int(row['population']):,}<br>"
                    f"Affected share: {row['fraction']:.2%}<br>"
                    f"Contributing pop: {int(row['population_contrib']):,}"
                ),
            ).add_to(m)

    # ---------- WIND DATA ----------
    # Generate wind field for canvas animation
    u, v, lat_grid, lon_grid = generate_wind_field(
        wind_speed_mph, wind_direction_deg, lat, lon, 
        size=WIND_GRID_SIZE, span=WIND_GRID_SPAN
    )
    
    # Return wind and fire data for later use
    wind_data = {
        'u': u,
        'v': v,
        'lat_grid': lat_grid,
        'lon_grid': lon_grid,
        'map_id': map_id,
        'wind_direction_deg': wind_direction_deg,
        # Fire animation data
        'center_lat': lat,
        'center_lon': lon,
        'ellipse_coords': ellipse_coords_latlon
    }

    return total_pop, table_sorted, m, wind_data


def save_map_with_wind(m: folium.Map, wind_data: dict, output_file: str):
    """
    Save map with wind animation and fire animation.
    
    Args:
        m: Folium Map object
        wind_data: Dictionary with wind and fire data
        output_file: Output filename
    """
    # Save map
    m.save(output_file)
    
    # Convert wind data to JSON
    u_json = json.dumps(wind_data['u'])
    v_json = json.dumps(wind_data['v'])
    lat_json = json.dumps(wind_data['lat_grid'])
    lon_json = json.dumps(wind_data['lon_grid'])
    
    # Generate wind script
    wind_script = generate_wind_script(
        wind_data['map_id'],
        u_json, v_json, lat_json, lon_json,
        wind_data['wind_direction_deg']
    )
    
    # Generate fire animation script
    fire_script = generate_fire_animation_script(
        wind_data['map_id'],
        wind_data['center_lat'],
        wind_data['center_lon'],
        wind_data['ellipse_coords'],
        wind_data['wind_direction_deg'],
        animation_duration_sec=12.0  # 12 seconds animation
    )
    
    # Insert scripts into HTML file
    try:
        with open(output_file, "r", encoding="utf-8") as f:
            html_content = f.read()
        
        if "</body>" in html_content:
            # Insert both animations
            all_scripts = fire_script + "\n" + wind_script
            html_content = html_content.replace("</body>", all_scripts + "\n</body>")
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(html_content)
        else:
            print(f"Warning: </body> tag not found in {output_file}")
            
    except IOError as e:
        print(f"Error writing file: {e}")


# ---------------------------------------------------------
# 8. Example / Main
# ---------------------------------------------------------
if __name__ == "__main__":
    # Parameters
    lat = 40.7128
    lon = -74.0060
    radius_km = 10
    wind_speed_mph = 10          # Speed
    wind_direction_deg = 135     # Direction: Wind from SE → Fire spreads NW
    
    # Debug: Show angle calculation
    fire_spread = (wind_direction_deg + 180) % 360
    angle = 90 - fire_spread
    print(f"Wind from: {wind_direction_deg}° → Fire to: {fire_spread}°")
    print(f"Mathematical angle: {angle}° (cos={math.cos(math.radians(angle)):.2f}, sin={math.sin(math.radians(angle)):.2f})")

    try:
        # Load data
        print("Loading data...")
        gdf = load_county_data(COUNTIES_FILE, POPULATION_FILE)
        print(f"  {len(gdf)} counties loaded")
        
        # Create map
        print("Creating map...")
        total_pop, table, m, wind_data = population_map(
            gdf, lat, lon, radius_km, wind_speed_mph, wind_direction_deg
        )
        
        print(f"Population inside {radius_km} km: {total_pop:,.0f}")
        if not table.empty:
            print(table[['COUNTY', 'STATE', 'population', 'fraction', 'population_contrib']].head())
        
        # Save map with wind
        print(f"Saving map to {OUTPUT_FILE}...")
        save_map_with_wind(m, wind_data, OUTPUT_FILE)
        print(f"Saved: {OUTPUT_FILE}")
        
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except ValueError as e:
        print(f"Data error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)
