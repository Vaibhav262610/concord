'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { cn } from '@/lib/utils';
import {
  LayoutDashboard,
  Users,
  GitBranch,
  Send,
  BarChart3,
  Settings,
  Menu,
  X,
  Zap,
} from 'lucide-react';

interface NavItem {
  href: string;
  label: string;
  icon: React.ReactNode;
}

const navItems: NavItem[] = [
  {
    href: '/dashboard',
    label: 'Overview',
    icon: <LayoutDashboard className="w-5 h-5" />,
  },
  {
    href: '/dashboard/agents',
    label: 'Agents',
    icon: <Users className="w-5 h-5" />,
  },
  {
    href: '/dashboard/decisions',
    label: 'Decisions',
    icon: <GitBranch className="w-5 h-5" />,
  },
  {
    href: '/dashboard/executions',
    label: 'Executions',
    icon: <Send className="w-5 h-5" />,
  },
  {
    href: '/dashboard/metrics',
    label: 'Metrics',
    icon: <BarChart3 className="w-5 h-5" />,
  },
  {
    href: '/dashboard/simulation',
    label: 'Simulation',
    icon: <Zap className="w-5 h-5" />,
  },
  {
    href: '/dashboard/actions',
    label: 'New Action',
    icon: <Settings className="w-5 h-5" />,
  },
];

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 sticky top-0 z-40">
        <div className="px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center">
              <button
                type="button"
                className="lg:hidden -ml-2 mr-2 p-2 rounded-md text-gray-400 hover:text-gray-500 hover:bg-gray-100"
                onClick={() => setSidebarOpen(!sidebarOpen)}
              >
                {sidebarOpen ? (
                  <X className="w-6 h-6" />
                ) : (
                  <Menu className="w-6 h-6" />
                )}
              </button>
              <Link href="/dashboard" className="flex items-center space-x-3">
                <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
                  <span className="text-white font-bold text-sm">C</span>
                </div>
                <div>
                  <h1 className="text-xl font-bold text-gray-900">CONCORD</h1>
                  <p className="text-xs text-gray-500">Agent Control Plane</p>
                </div>
              </Link>
            </div>

            <div className="flex items-center space-x-4">
              <div className="hidden sm:block">
                <div className="flex items-center space-x-2">
                  <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                  <span className="text-sm text-gray-600">System Operational</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </header>

      <div className="flex">
        {/* Sidebar */}
        <aside
          className={cn(
            'fixed inset-y-0 left-0 z-30 w-64 bg-white border-r border-gray-200 transform transition-transform duration-200 ease-in-out lg:translate-x-0 lg:static lg:inset-0',
            sidebarOpen ? 'translate-x-0' : '-translate-x-full'
          )}
        >
          <nav className="mt-16 lg:mt-5 px-4 space-y-1">
            {navItems.map((item) => {
              const isActive = pathname === item.href;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  onClick={() => setSidebarOpen(false)}
                  className={cn(
                    'flex items-center space-x-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors',
                    isActive
                      ? 'bg-blue-50 text-blue-700'
                      : 'text-gray-700 hover:bg-gray-50 hover:text-gray-900'
                  )}
                >
                  {item.icon}
                  <span>{item.label}</span>
                </Link>
              );
            })}
          </nav>

          {/* Sidebar Footer */}
          <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-gray-200">
            <div className="text-xs text-gray-500 space-y-1">
              <p className="font-semibold">CONCORD v1.0</p>
              <p>Razorpay AI Buildathon 2026</p>
              <p className="text-green-600 font-medium">✓ All Phases Complete</p>
            </div>
          </div>
        </aside>

        {/* Overlay for mobile */}
        {sidebarOpen && (
          <div
            className="fixed inset-0 bg-gray-600 bg-opacity-50 z-20 lg:hidden"
            onClick={() => setSidebarOpen(false)}
          ></div>
        )}

        {/* Main Content */}
        <main className="flex-1 lg:ml-0">
          <div className="py-6 px-4 sm:px-6 lg:px-8">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}
