'use client';

import React, { useEffect, useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { api, type Decision, type Execution, type DeliveryMetrics } from '@/lib/api';
import { formatNumber, formatPercentage, getDecisionColor, getChannelIcon } from '@/lib/utils';
import { Users, GitBranch, Send, TrendingUp, Clock, CheckCircle2, XCircle, Loader2 } from 'lucide-react';

export default function DashboardPage() {
  const [stats, setStats] = useState({
    totalAgents: 0,
    totalDecisions: 0,
    totalExecutions: 0,
    successRate: 0,
  });
  const [recentDecisions, setRecentDecisions] = useState<Decision[]>([]);
  const [recentExecutions, setRecentExecutions] = useState<Execution[]>([]);
  const [metrics, setMetrics] = useState<DeliveryMetrics | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDashboardData();
    // Auto-refresh every 30 seconds
    const interval = setInterval(loadDashboardData, 30000);
    return () => clearInterval(interval);
  }, []);

  async function loadDashboardData() {
    try {
      const [agentsData, decisionsData, executionsData, metricsData] = await Promise.all([
        api.listAgents({ limit: 1 }),
        api.listDecisions({ limit: 5 }),
        api.listExecutions({ limit: 5 }),
        api.getDeliveryMetrics(),
      ]);

      setStats({
        totalAgents: agentsData.total,
        totalDecisions: decisionsData.total,
        totalExecutions: executionsData.total,
        successRate: metricsData.success_rate || 0,
      });

      setRecentDecisions(decisionsData.decisions);
      setRecentExecutions(executionsData.executions);
      setMetrics(metricsData);
    } catch (error) {
      console.error('Failed to load dashboard data:', error);
    } finally {
      setLoading(false);
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <Loader2 className="w-8 h-8 animate-spin text-blue-500" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Dashboard Overview</h1>
        <p className="mt-2 text-gray-600">
          Real-time monitoring of your agent fleet control plane
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Agents</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatNumber(stats.totalAgents)}</div>
            <p className="text-xs text-muted-foreground">Active in fleet</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Decisions Made</CardTitle>
            <GitBranch className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatNumber(stats.totalDecisions)}</div>
            <p className="text-xs text-muted-foreground">Arbitration decisions</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Executions</CardTitle>
            <Send className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatNumber(stats.totalExecutions)}</div>
            <p className="text-xs text-muted-foreground">Messages sent</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Success Rate</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatPercentage(stats.successRate)}</div>
            <p className="text-xs text-muted-foreground">Delivery success</p>
          </CardContent>
        </Card>
      </div>

      {/* Channel Breakdown */}
      {metrics && Object.keys(metrics.by_channel).length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Channel Performance</CardTitle>
            <CardDescription>Delivery metrics by communication channel</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {Object.entries(metrics.by_channel).map(([channel, data]) => (
                <div key={channel} className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <span className="text-2xl">{getChannelIcon(channel)}</span>
                    <div>
                      <p className="font-medium">{channel}</p>
                      <p className="text-sm text-gray-500">
                        {formatNumber(data.delivered)} / {formatNumber(data.total)} delivered
                      </p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="font-semibold text-lg">{formatPercentage(data.success_rate)}</p>
                    <p className="text-xs text-gray-500">success rate</p>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Recent Activity */}
      <div className="grid gap-6 lg:grid-cols-2">
        {/* Recent Decisions */}
        <Card>
          <CardHeader>
            <CardTitle>Recent Decisions</CardTitle>
            <CardDescription>Latest arbitration outcomes</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {recentDecisions.length === 0 ? (
                <p className="text-sm text-gray-500 text-center py-4">No decisions yet</p>
              ) : (
                recentDecisions.map((decision) => (
                  <div key={decision.id} className="flex items-start justify-between border-b border-gray-100 pb-3 last:border-0">
                    <div className="flex-1">
                      <div className="flex items-center space-x-2">
                        <Badge className={getDecisionColor(decision.decision_type)}>
                          {decision.decision_type}
                        </Badge>
                        <span className="text-sm font-medium">Score: {decision.final_score.toFixed(0)}</span>
                      </div>
                      <p className="text-sm text-gray-600 mt-1">{decision.decision_reason}</p>
                    </div>
                  </div>
                ))
              )}
            </div>
          </CardContent>
        </Card>

        {/* Recent Executions */}
        <Card>
          <CardHeader>
            <CardTitle>Recent Executions</CardTitle>
            <CardDescription>Latest message deliveries</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {recentExecutions.length === 0 ? (
                <p className="text-sm text-gray-500 text-center py-4">No executions yet</p>
              ) : (
                recentExecutions.map((execution) => (
                  <div key={execution.id} className="flex items-center justify-between border-b border-gray-100 pb-3 last:border-0">
                    <div className="flex items-center space-x-3">
                      <span className="text-xl">{getChannelIcon(execution.channel)}</span>
                      <div>
                        <p className="text-sm font-medium">{execution.channel}</p>
                        <p className="text-xs text-gray-500">
                          {execution.status}
                        </p>
                      </div>
                    </div>
                    {execution.result === 'success' ? (
                      <CheckCircle2 className="w-5 h-5 text-green-500" />
                    ) : execution.result === 'failed' ? (
                      <XCircle className="w-5 h-5 text-red-500" />
                    ) : (
                      <Clock className="w-5 h-5 text-yellow-500" />
                    )}
                  </div>
                ))
              )}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
