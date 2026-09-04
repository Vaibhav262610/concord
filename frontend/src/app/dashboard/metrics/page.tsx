'use client';

import React, { useEffect, useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { api, type DeliveryMetrics } from '@/lib/api';
import { formatNumber, formatPercentage, getChannelIcon } from '@/lib/utils';
import { Loader2, RefreshCw, TrendingUp, Send, CheckCircle2, XCircle } from 'lucide-react';
import { BarChart, Bar, PieChart, Pie, Cell, ResponsiveContainer, XAxis, YAxis, Tooltip, Legend } from 'recharts';

const COLORS = ['#10b981', '#3b82f6', '#8b5cf6', '#f59e0b', '#ef4444'];

export default function MetricsPage() {
  const [metrics, setMetrics] = useState<DeliveryMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    loadMetrics();
    // Auto-refresh every 30 seconds
    const interval = setInterval(() => loadMetrics(true), 30000);
    return () => clearInterval(interval);
  }, []);

  async function loadMetrics(silent = false) {
    if (!silent) setLoading(true);
    else setRefreshing(true);

    try {
      const data = await api.getDeliveryMetrics();
      setMetrics(data);
    } catch (error) {
      console.error('Failed to load metrics:', error);
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

  if (!metrics) {
    return (
      <div className="flex items-center justify-center h-96">
        <p className="text-gray-500">No metrics data available</p>
      </div>
    );
  }

  // Prepare chart data
  const channelData = Object.entries(metrics.by_channel).map(([channel, data]) => ({
    channel,
    total: data.total,
    sent: data.sent,
    delivered: data.delivered,
    failed: data.failed,
    successRate: data.success_rate,
  }));

  const statusData = Object.entries(metrics.by_status).map(([status, count]) => ({
    name: status,
    value: count,
  }));

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
            <CardTitle className="text-sm font-medium">Success Rate</CardTitle>
            <TrendingUp className="h-4 w-4 text-green-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">
              {formatPercentage(metrics.success_rate)}
            </div>
            <p className="text-xs text-muted-foreground">Overall delivery</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Delivered</CardTitle>
            <CheckCircle2 className="h-4 w-4 text-green-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">
              {formatNumber(metrics.by_status['delivered'] || 0)}
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
              {formatNumber(metrics.by_status['failed'] || 0)}
            </div>
            <p className="text-xs text-muted-foreground">Failed deliveries</p>
          </CardContent>
        </Card>
      </div>

      {/* Channel Performance Bar Chart */}
      {channelData.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Channel Performance</CardTitle>
            <CardDescription>Success rate by communication channel</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-80">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={channelData}>
                  <XAxis dataKey="channel" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Bar dataKey="delivered" fill="#10b981" name="Delivered" />
                  <Bar dataKey="failed" fill="#ef4444" name="Failed" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Status Distribution Pie Chart */}
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
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
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

      {/* Detailed Channel Breakdown */}
      <Card>
        <CardHeader>
          <CardTitle>Detailed Channel Metrics</CardTitle>
          <CardDescription>Comprehensive statistics for each channel</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-6">
            {channelData.map((channel, index) => (
              <div key={channel.channel} className="border-b border-gray-100 pb-6 last:border-0">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center space-x-3">
                    <span className="text-3xl">{getChannelIcon(channel.channel)}</span>
                    <div>
                      <h3 className="text-lg font-semibold">{channel.channel}</h3>
                      <p className="text-sm text-gray-500">
                        {formatNumber(channel.total)} total executions
                      </p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-2xl font-bold text-gray-900">
                      {formatPercentage(channel.successRate)}
                    </p>
                    <p className="text-sm text-gray-500">Success Rate</p>
                  </div>
                </div>

                <div className="grid grid-cols-3 gap-4">
                  <div className="bg-blue-50 rounded-lg p-4 text-center">
                    <p className="text-sm text-blue-600 font-medium mb-1">Sent</p>
                    <p className="text-2xl font-bold text-blue-900">{formatNumber(channel.sent)}</p>
                  </div>
                  <div className="bg-green-50 rounded-lg p-4 text-center">
                    <p className="text-sm text-green-600 font-medium mb-1">Delivered</p>
                    <p className="text-2xl font-bold text-green-900">{formatNumber(channel.delivered)}</p>
                  </div>
                  <div className="bg-red-50 rounded-lg p-4 text-center">
                    <p className="text-sm text-red-600 font-medium mb-1">Failed</p>
                    <p className="text-2xl font-bold text-red-900">{formatNumber(channel.failed)}</p>
                  </div>
                </div>

                {/* Progress Bar */}
                <div className="mt-4">
                  <div className="h-4 bg-gray-200 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-green-500 transition-all duration-500"
                      style={{ width: `${channel.successRate}%` }}
                    ></div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Summary Card */}
      <Card className="bg-gradient-to-r from-purple-50 to-blue-50">
        <CardContent className="py-6">
          <div className="text-center">
            <p className="text-sm text-gray-600 mb-2">Reporting Period</p>
            <p className="text-xl font-semibold text-gray-900">{metrics.period || 'All Time'}</p>
            <p className="text-sm text-gray-500 mt-4">
              Data refreshes automatically every 30 seconds
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
