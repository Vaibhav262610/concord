'use client';

import React, { useEffect, useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { api, type DeliveryMetrics } from '@/lib/api';
import { formatNumber, formatPercentage } from '@/lib/utils';
import { Loader2, RefreshCw, TrendingUp, Send, CheckCircle2, XCircle, AlertTriangle } from 'lucide-react';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend } from 'recharts';

const COLORS = ['#10b981', '#ef4444', '#f59e0b', '#8b5cf6'];

export default function MetricsPage() {
  const [metrics, setMetrics] = useState<DeliveryMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadMetrics();
    // Auto-refresh every 30 seconds
    const interval = setInterval(() => loadMetrics(true), 30000);
    return () => clearInterval(interval);
  }, []);

  async function loadMetrics(silent = false) {
    if (!silent) setLoading(true);
    else setRefreshing(true);
    setError(null);

    try {
      const data = await api.getDeliveryMetrics();
      setMetrics(data);
    } catch (error) {
      console.error('Failed to load metrics:', error);
      setError('Failed to load metrics data');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <Loader2 className="w-8 h-8 animate-spin text-blue-500" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center h-96">
        <p className="text-red-500 mb-4">{error}</p>
        <Button onClick={() => loadMetrics()}>
          <RefreshCw className="w-4 h-4 mr-2" />
          Retry
        </Button>
      </div>
    );
  }

  if (!metrics) {
    return (
      <div className="flex items-center justify-center h-96">
        <p className="text-gray-500">No metrics data available</p>
      </div>
    );
  }

  // Prepare chart data
  const statusData = [
    { name: 'Delivered', value: metrics.delivered, color: '#10b981' },
    { name: 'Failed', value: metrics.failed, color: '#ef4444' },
    { name: 'Bounced', value: metrics.bounced, color: '#f59e0b' },
    { name: 'Sent (Pending)', value: metrics.sent - metrics.delivered - metrics.failed, color: '#8b5cf6' },
  ].filter(item => item.value > 0);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Delivery Metrics</h1>
          <p className="mt-2 text-gray-600">
            Comprehensive analytics for message delivery performance
          </p>
        </div>
        <Button
          variant="outline"
          onClick={() => loadMetrics()}
          disabled={refreshing}
        >
          <RefreshCw className={`w-4 h-4 mr-2 ${refreshing ? 'animate-spin' : ''}`} />
          Refresh
        </Button>
      </div>

      {/* Overview Stats */}
      <div className="grid gap-6 md:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Executions</CardTitle>
            <Send className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatNumber(metrics.total_executions)}</div>
            <p className="text-xs text-muted-foreground">All channels</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Delivery Rate</CardTitle>
            <TrendingUp className="h-4 w-4 text-green-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">
              {formatPercentage(metrics.delivery_rate)}
            </div>
            <p className="text-xs text-muted-foreground">Successfully delivered</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Delivered</CardTitle>
            <CheckCircle2 className="h-4 w-4 text-green-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">
              {formatNumber(metrics.delivered)}
            </div>
            <p className="text-xs text-muted-foreground">Successful deliveries</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Failed</CardTitle>
            <XCircle className="h-4 w-4 text-red-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-600">
              {formatNumber(metrics.failed)}
            </div>
            <p className="text-xs text-muted-foreground">Failed deliveries</p>
          </CardContent>
        </Card>
      </div>

      {/* Status Distribution */}
      <div className="grid gap-6 md:grid-cols-2">
        {statusData.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle>Status Distribution</CardTitle>
              <CardDescription>Breakdown of execution statuses</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="h-80">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={statusData}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={(entry) => `${entry.name}: ${entry.value}`}
                      outerRadius={100}
                      fill="#8884d8"
                      dataKey="value"
                    >
                      {statusData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip />
                    <Legend />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>
        )}

        <Card>
          <CardHeader>
            <CardTitle>Performance Metrics</CardTitle>
            <CardDescription>Detailed delivery statistics</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="space-y-4">
              <div className="flex items-center justify-between pb-2 border-b">
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full bg-blue-500"></div>
                  <span className="text-sm font-medium">Sent</span>
                </div>
                <span className="text-lg font-bold">{formatNumber(metrics.sent)}</span>
              </div>

              <div className="flex items-center justify-between pb-2 border-b">
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full bg-green-500"></div>
                  <span className="text-sm font-medium">Delivered</span>
                </div>
                <span className="text-lg font-bold text-green-600">{formatNumber(metrics.delivered)}</span>
              </div>

              <div className="flex items-center justify-between pb-2 border-b">
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full bg-red-500"></div>
                  <span className="text-sm font-medium">Failed</span>
                </div>
                <span className="text-lg font-bold text-red-600">{formatNumber(metrics.failed)}</span>
              </div>

              <div className="flex items-center justify-between pb-2 border-b">
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full bg-orange-500"></div>
                  <span className="text-sm font-medium">Bounced</span>
                </div>
                <span className="text-lg font-bold text-orange-600">{formatNumber(metrics.bounced)}</span>
              </div>
            </div>

            <div className="pt-4 space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">Delivery Rate</span>
                <span className="text-sm font-semibold text-green-600">
                  {formatPercentage(metrics.delivery_rate)}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">Failure Rate</span>
                <span className="text-sm font-semibold text-red-600">
                  {formatPercentage(metrics.failure_rate)}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">Bounce Rate</span>
                <span className="text-sm font-semibold text-orange-600">
                  {formatPercentage(metrics.bounce_rate)}
                </span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Summary Card */}
      <Card className="bg-gradient-to-r from-purple-50 to-blue-50">
        <CardContent className="py-6">
          <div className="text-center">
            <p className="text-sm text-gray-600 mb-2">Reporting Period</p>
            <p className="text-lg font-semibold text-gray-900">
              {new Date(metrics.start_date).toLocaleDateString()} - {new Date(metrics.end_date).toLocaleDateString()}
            </p>
            <p className="text-sm text-gray-500 mt-4">
              Data refreshes automatically every 30 seconds
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
