'use client';

import React, { useEffect, useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { api, type Execution } from '@/lib/api';
import { formatDate, formatRelativeTime, getExecutionStatusColor, getChannelIcon } from '@/lib/utils';
import { Loader2, RefreshCw, CheckCircle2, XCircle, Clock, Send } from 'lucide-react';

export default function ExecutionsPage() {
  const [executions, setExecutions] = useState<Execution[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [filterChannel, setFilterChannel] = useState<string>('ALL');
  const [filterStatus, setFilterStatus] = useState<string>('ALL');

  useEffect(() => {
    loadExecutions();
    // Auto-refresh every 15 seconds
    const interval = setInterval(() => loadExecutions(true), 15000);
    return () => clearInterval(interval);
  }, [filterChannel, filterStatus]);

  async function loadExecutions(silent = false) {
    if (!silent) setLoading(true);
    else setRefreshing(true);

    try {
      const params: any = { limit: 100 };
      if (filterChannel !== 'ALL') params.channel = filterChannel;
      if (filterStatus !== 'ALL') params.status = filterStatus;

      const data = await api.listExecutions(params);
      setExecutions(data.executions);
    } catch (error) {
      console.error('Failed to load executions:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }

  function getStatusIcon(execution: Execution) {
    const status = execution.status.toLowerCase();
    if (status === 'sent' || status === 'delivered' || status === 'processed') {
      return <CheckCircle2 className="w-5 h-5 text-green-500" />;
    } else if (status === 'failed' || status === 'bounced' || status === 'expired') {
      return <XCircle className="w-5 h-5 text-red-500" />;
    } else if (status === 'pending' || status === 'queued') {
      return <Clock className="w-5 h-5 text-yellow-500" />;
    }
    return <Send className="w-5 h-5 text-blue-500" />;
  }

  const channels = ['ALL', 'EMAIL', 'SMS', 'WHATSAPP', 'PUSH'];
  const statuses = ['ALL', 'pending', 'processed', 'sent', 'failed'];

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
          <h1 className="text-3xl font-bold text-gray-900">Execution Tracking</h1>
          <p className="mt-2 text-gray-600">
            Monitor message delivery across all channels
          </p>
        </div>
        <Button
          variant="outline"
          onClick={() => loadExecutions()}
          disabled={refreshing}
        >
          <RefreshCw className={`w-4 h-4 mr-2 ${refreshing ? 'animate-spin' : ''}`} />
          Refresh
        </Button>
      </div>

      {/* Filters */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Filters</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Channel</label>
            <div className="flex flex-wrap gap-2">
              {channels.map((channel) => (
                <Button
                  key={channel}
                  variant={filterChannel === channel ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setFilterChannel(channel)}
                >
                  {channel === 'ALL' ? 'All Channels' : `${getChannelIcon(channel)} ${channel}`}
                </Button>
              ))}
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Status</label>
            <div className="flex flex-wrap gap-2">
              {statuses.map((status) => (
                <Button
                  key={status}
                  variant={filterStatus === status ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setFilterStatus(status)}
                >
                  {status === 'ALL' ? 'All Statuses' : status}
                </Button>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Executions List */}
      <div className="space-y-4">
        {executions.length === 0 ? (
          <Card>
            <CardContent className="py-12 text-center">
              <p className="text-gray-500">No executions found for the selected filters.</p>
            </CardContent>
          </Card>
        ) : (
          executions.map((execution) => (
            <Card key={execution.id} className="hover:shadow-md transition-shadow">
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div className="space-y-2 flex-1">
                    <div className="flex items-center space-x-3">
                      {getStatusIcon(execution)}
                      <span className="text-2xl">{getChannelIcon(execution.channel)}</span>
                      <div>
                        <h3 className="text-lg font-semibold">{execution.channel}</h3>
                        <Badge className={getExecutionStatusColor(execution.status)}>
                          {execution.status}
                        </Badge>
                      </div>
                    </div>
                  </div>
                  <div className="text-right text-sm text-gray-500">
                    <p>{formatRelativeTime(execution.scheduled_at)}</p>
                    <p className="text-xs">{formatDate(execution.scheduled_at)}</p>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {/* Timing Information */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="bg-blue-50 rounded-lg p-3">
                      <p className="text-xs text-blue-600 font-medium mb-1">Scheduled At</p>
                      <p className="text-sm font-semibold text-blue-900">
                        {formatDate(execution.scheduled_at)}
                      </p>
                    </div>
                    {execution.executed_at && (
                      <div className="bg-green-50 rounded-lg p-3">
                        <p className="text-xs text-green-600 font-medium mb-1">Executed At</p>
                        <p className="text-sm font-semibold text-green-900">
                          {formatDate(execution.executed_at)}
                        </p>
                      </div>
                    )}
                  </div>

                  {/* Result */}
                  {execution.result && (
                    <div className={`rounded-lg p-3 ${
                      execution.result === 'success' ? 'bg-green-50' : 'bg-red-50'
                    }`}>
                      <p className={`text-xs font-medium mb-1 ${
                        execution.result === 'success' ? 'text-green-600' : 'text-red-600'
                      }`}>
                        Result
                      </p>
                      <p className={`text-sm font-semibold ${
                        execution.result === 'success' ? 'text-green-900' : 'text-red-900'
                      }`}>
                        {execution.result === 'success' ? '✓ Success' : '✗ Failed'}
                      </p>
                    </div>
                  )}

                  {/* Metadata */}
                  {execution.metadata && Object.keys(execution.metadata).length > 0 && (
                    <div className="pt-2 border-t border-gray-100">
                      <p className="text-xs font-medium text-gray-700 mb-2">Additional Details</p>
                      <div className="bg-gray-50 rounded p-2">
                        <pre className="text-xs text-gray-600 overflow-x-auto">
                          {JSON.stringify(execution.metadata, null, 2)}
                        </pre>
                      </div>
                    </div>
                  )}

                  {/* IDs */}
                  <div className="pt-2 border-t border-gray-100">
                    <p className="text-xs text-gray-500">
                      Execution ID: <code className="text-xs bg-gray-100 px-2 py-0.5 rounded">{execution.id}</code>
                    </p>
                    <p className="text-xs text-gray-500 mt-1">
                      Request ID: <code className="text-xs bg-gray-100 px-2 py-0.5 rounded">{execution.request_id}</code>
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))
        )}
      </div>

      {/* Summary Stats */}
      {executions.length > 0 && (
        <Card className="bg-gradient-to-r from-green-50 to-blue-50">
          <CardContent className="py-6">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
              <div>
                <p className="text-sm text-gray-600 mb-1">Total</p>
                <p className="text-2xl font-bold text-gray-900">{executions.length}</p>
              </div>
              <div>
                <p className="text-sm text-gray-600 mb-1">Success</p>
                <p className="text-2xl font-bold text-green-600">
                  {executions.filter(e => e.result === 'success').length}
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-600 mb-1">Failed</p>
                <p className="text-2xl font-bold text-red-600">
                  {executions.filter(e => e.result === 'failed').length}
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-600 mb-1">Pending</p>
                <p className="text-2xl font-bold text-yellow-600">
                  {executions.filter(e => !e.result || e.status === 'pending').length}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
