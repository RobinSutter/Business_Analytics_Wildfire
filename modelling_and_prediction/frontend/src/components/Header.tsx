import { useState } from 'react';
import { Flame, Moon, Sun, History, Camera, BarChart3, Menu, X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useTheme } from '@/hooks/useTheme';
import { NavLink } from '@/components/NavLink';
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from '@/components/ui/sheet';

interface HeaderProps {
  onHistoryClick: () => void;
  historyCount: number;
}

export function Header({ onHistoryClick, historyCount }: HeaderProps) {
  const { theme, toggleTheme } = useTheme();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  return (
    <header className="sticky top-0 z-50 w-full border-b border-border/50 bg-card/80 backdrop-blur-xl">
      <div className="container mx-auto px-4">
        <div className="flex h-16 items-center justify-between">
          {/* Logo */}
          <div className="flex items-center gap-6">
            <div className="flex items-center gap-3">
              <div className="relative">
                <div className="absolute inset-0 bg-gradient-to-br from-fire-red to-fire-orange rounded-xl blur-lg opacity-50 animate-fire-flicker" />
                <div className="relative flex items-center justify-center w-10 h-10 bg-gradient-to-br from-fire-red to-fire-orange rounded-xl shadow-lg">
                  <Flame className="w-6 h-6 text-white" />
                </div>
              </div>
              <div>
                <h1 className="text-xl font-bold tracking-tight">
                  <span className="fire-gradient-text">FSP</span>
                  <span className="text-foreground ml-1">Fire Size Predictor</span>
                </h1>
                <p className="text-xs text-muted-foreground">Fire Marshal's Decision Support System</p>
              </div>
            </div>

            {/* Navigation */}
            <nav className="hidden md:flex items-center gap-1">
              <NavLink
                to="/"
                className="px-4 py-2 rounded-lg text-sm font-medium transition-colors hover:bg-accent"
                activeClassName="bg-accent"
              >
                <div className="flex items-center gap-2">
                  <BarChart3 className="w-4 h-4" />
                  <span>Prediction</span>
                </div>
              </NavLink>
              <NavLink
                to="/webcam"
                className="px-4 py-2 rounded-lg text-sm font-medium transition-colors hover:bg-accent"
                activeClassName="bg-accent"
              >
                <div className="flex items-center gap-2">
                  <Camera className="w-4 h-4" />
                  <span>Webcam</span>
                </div>
              </NavLink>
            </nav>
          </div>

          {/* Actions */}
          <div className="flex items-center gap-2">
            {/* Mobile Menu */}
            <Sheet open={mobileMenuOpen} onOpenChange={setMobileMenuOpen}>
              <SheetTrigger asChild>
                <Button variant="ghost" size="icon" className="md:hidden">
                  <Menu className="w-5 h-5" />
                </Button>
              </SheetTrigger>
              <SheetContent side="right">
                <SheetHeader>
                  <SheetTitle>Menu</SheetTitle>
                </SheetHeader>
                <nav className="flex flex-col gap-2 mt-6">
                  <NavLink
                    to="/"
                    onClick={() => setMobileMenuOpen(false)}
                    className="flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-colors hover:bg-accent"
                    activeClassName="bg-accent"
                  >
                    <BarChart3 className="w-5 h-5" />
                    <span>Prediction</span>
                  </NavLink>
                  <NavLink
                    to="/webcam"
                    onClick={() => setMobileMenuOpen(false)}
                    className="flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-colors hover:bg-accent"
                    activeClassName="bg-accent"
                  >
                    <Camera className="w-5 h-5" />
                    <span>Webcam</span>
                  </NavLink>
                  <Button
                    variant="ghost"
                    onClick={() => {
                      setMobileMenuOpen(false);
                      onHistoryClick();
                    }}
                    className="justify-start gap-3 px-4 py-3 h-auto"
                  >
                    <History className="w-5 h-5" />
                    <span>History</span>
                    {historyCount > 0 && (
                      <span className="ml-auto px-2 py-0.5 bg-primary text-primary-foreground text-xs rounded-full font-bold">
                        {historyCount > 9 ? '9+' : historyCount}
                      </span>
                    )}
                  </Button>
                </nav>
              </SheetContent>
            </Sheet>

            {/* Desktop Actions */}
            <Button
              variant="glass"
              size="sm"
              onClick={onHistoryClick}
              className="relative hidden md:flex"
            >
              <History className="w-4 h-4" />
              <span className="hidden sm:inline">History</span>
              {historyCount > 0 && (
                <span className="absolute -top-1 -right-1 w-5 h-5 bg-primary text-primary-foreground text-xs rounded-full flex items-center justify-center font-bold">
                  {historyCount > 9 ? '9+' : historyCount}
                </span>
              )}
            </Button>
            
            <Button
              variant="ghost"
              size="icon"
              onClick={toggleTheme}
              className="rounded-full"
            >
              {theme === 'dark' ? (
                <Sun className="w-5 h-5" />
              ) : (
                <Moon className="w-5 h-5" />
              )}
            </Button>
          </div>
        </div>
      </div>
    </header>
  );
}
