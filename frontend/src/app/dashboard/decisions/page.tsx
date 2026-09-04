'use client';

import React, { useEffect, useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { api, type Decision } from '@/lib/api';
import { formatDate, formatRelativeTime, getDecisionColor, formatNumber } from '@/lib/utils';
import { Loader2, RefreshCw, Filter, TrendingUp, TrendingDown, Minus } from 'lucide-react';

export default function DecisionsPage() {
  const [decisions, setDecisions] = useState<Decision[]>([]);
  const [filteredDecisions, setFilteredDecisions] = useState<Decision[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [filterType, setFilterType] = useState<'ALL' | 'ALLOW' | 'BLOCK' | 'DELAY'>('ALL');
  const [stats, setStats] = useState({
    total: 0,
    allow: 0,
    block: 0,
    delay: 0,
    avgScore: 0,
  });

  useEffect(() => {
    loadDecisions();
    // Auto-refresh every 10 seconds
    const interval = setInterval(() => loadDecisions(true), 10000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    applyFilter();
  }, [decisions, filterType]);

  async function loadDecisions(silent = false) {
    if (!silent) setLoading(true);
    else setRefreshing(true);

    try {
      const data = await api.listDecisions({ limit: 100 });
      setDecisions(data.decisions);

      // Calculate stats
      const allow = data.decisions.filter(d => d.decision_type === 'ALLOW').length;
      const block = data.decisions.filter(d => d.decision_type === 'BLOCK').length;
      const delay = data.decisions.filter(d => d.decision_type === 'DELAY').length;
      const avgScore = data.decisions.length > 0
        ? data.decisions.reduce((sum, d) => sum + d.final_score, 0) / data.decisions.length
        : 0;

      setStats({
        total: data.total,
        allow,
        block,
        delay,
        avgScore,
      });
    } catch (error) {
      console.error('Failed to load decisions:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }

  function applyFilter() {
    if (filterType === 'ALL') {
      setFilteredDecisions(decisions);
    } else {
      setFilteredDecisions(decisions.filter(d => d.decision_type === filterType));
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
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Arbitration Decisions</h1>
          <p className="mt-2 text-gray-600">
            Real-time decision monitoring from the arbitration engine
          </p>
        </div>
        <Button
          variant="outline"
          onClick={() => loadDecisions()}
          disabled={refreshing}
        >
          <RefreshCw className={`w-4 h-4 mr-2 ${refreshing ? 'animate-spin' : ''}`} />
          Refresh
        </Button>
      </div>

      {/* Stats Cards */}
      <div className="grid gap-6 md:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Decisions</CardTitle>
            <Filter className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatNumber(stats.total)}</div>
            <p className="text-xs text-muted-foreground">All time</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Allowed</CardTitle>
            <TrendingUp className="h-4 w-4 text-green-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">{formatNumber(stats.allow)}</div>
            <p className="text-xs text-muted-foreground">
              {stats.total > 0 ? ((stats.allow / stats.total) * 100).toFixed(1) : 0}% of total
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Blocked</CardTitle>
            <TrendingDown className="h-4 w-4 text-red-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-600">{formatNumber(stats.block)}</div>
            <p className="text-xs text-muted-foreground">
              {stats.total > 0 ? ((stats.block / stats.total) * 100).toFixed(1) : 0}% of total
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Delayed</CardTitle>
            <Minus className="h-4 w-4 text-yellow-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-yellow-600">{formatNumber(stats.delay)}</div>
            <p className="text-xs text-muted-foreground">
              {stats.total > 0 ? ((stats.delay / stats.total) * 100).toFixed(1) : 0}% of total
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Filter Decisions</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-2">
            <Button
              variant={filterType === 'ALL' ? 'default' : 'outline'}
              size="sm"
              onClick={() => setFilterType('ALL')}
            >
              All ({decisions.length})
            </Button>
            <Button
              variant={filterType === 'ALLOW' ? 'default' : 'outline'}
              size="sm"
              onClick={() => setFilterType('ALLOW')}
            >
              Allow ({stats.allow})
            </Button>
            <Button
              variant={filterType === 'BLOCK' ? 'default' : 'outline'}
              size="sm"
              onClick={() => setFilterType('BLOCK')}
            >
              Block ({stats.block})
            </Button>
            <Button
              variant={filterType === 'DELAY' ? 'default' : 'outline'}
              size="sm"
              onClick={() => setFilterType('DELAY')}
            >
              Delay ({stats.delay})
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Decisions List */}
      <div className="space-y-4">
        {filteredDecisions.length === 0 ? (
          <Card>
            <CardContent className="py-12 text-center">
              <p className="text-gray-500">No decisions found for the selected filter.</p>
            </CardContent>
          </Card>
        ) : (
          filteredDecisions.map((decision) => (
            <Card key={decision.id} className="hover:shadow-md transition-shadow">
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div className="space-y-2 flex-1">
                    <div className="flex items-center space-x-3">
                      <Badge className={getDecisionColor(decision.decision_type)}>
                        {decision.decision_type}
                      </Badge>
                      <span className="text-sm font-medium text-gray-600">
                        Score: <span className="text-lg font-bold text-gray-900">{decision.final_score.toFixed(1)}</span>/100
                      </span>
                    </div>
                    <CardTitle className="text-lg">{decision.decision_reason}</CardTitle>
                    {decision.delay_reason && (
                      <CardDescription className="flex items-center space-x-2">
                        <span className="text-yellow-600">⏱️ Delay Reason:</span>
                        <span>{decision.delay_reason}</span>
                      </CardDescription>
                    )}
                  </div>
                  <div className="text-right text-sm text-gray-500">
                    <p>{formatRelativeTime(decision.created_at)}</p>
                    <p className="text-xs">{formatDate(decision.created_at)}</p>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {/* Score Breakdown */}
                  <div>
                    <h4 className="text-sm font-semibold text-gray-700 mb-2">Score Breakdown</h4>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                      <div className="bg-blue-50 rounded-lg p-3">
                        <p className="text-xs text-blue-600 font-medium">Priority</p>
                        <p className="text-lg font-bold text-blue-900">{decision.scores.priority_score.toFixed(1)}</p>
                      </div>
                      <div className="bg-green-50 rounded-lg p-3">
                        <p className="text-xs text-green-600 font-medium">Value</p>
                        <p className="text-lg font-bold text-green-900">{decision.scores.value_score.toFixed(1)}</p>
                      </div>
                      <div className="bg-purple-50 rounded-lg p-3">
                        <p className="text-xs text-purple-600 font-medium">Consent</p>
                        <p className="text-lg font-bold text-purple-900">{decision.scores.consent_score.toFixed(1)}</p>
                      </div>
                      <div className="bg-orange-50 rounded-lg p-3">
                        <p className="text-xs text-orange-600 font-medium">Frequency</p>
                        <p className="text-lg font-bold text-orange-900">{decision.scores.frequency_score.toFixed(1)}</p>
                      </div>
                    </div>
                  </div>

                  {/* Request ID */}
                  <div className="pt-2 border-t border-gray-100">
                    <p className="text-xs text-gray-500">
                      Request ID: <code className="text-xs bg-gray-100 px-2 py-0.5 rounded">{decision.request_id}</code>
                    </p>
                    <p className="text-xs text-gray-500 mt-1">
                      Decision ID: <code className="text-xs bg-gray-100 px-2 py-0.5 rounded">{decision.id}</code>
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))
        )}
      </div>

      {/* Average Score Summary */}
      {filteredDecisions.length > 0 && (
        <Card className="bg-gradient-to-r from-blue-50 to-purple-50">
          <CardContent className="py-6">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-semibold text-gray-900">Average Decision Score</h3>
                <p className="text-sm text-gray-600">Across {filteredDecisions.length} decisions</p>
              </div>
              <div className="text-4xl font-bold text-blue-600">
                {stats.avgScore.toFixed(1)}
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
