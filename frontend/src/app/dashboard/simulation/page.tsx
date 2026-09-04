"use client";

import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { api, SimulationScenario, SimulationResult, AgentFleetInfo } from '@/lib/api';
import { Play, Users, Clock, Zap, TrendingUp, AlertCircle } from 'lucide-react';

export default function SimulationPage() {
  const [scenarios, setScenarios] = useState<SimulationScenario[]>([]);
  const [fleetInfo, setFleetInfo] = useState<AgentFleetInfo | null>(null);
  const [selectedScenario, setSelectedScenario] = useState<string>('');
  const [customerCount, setCustomerCount] = useState<number>(10);
  const [duration, setDuration] = useState<number>(300);
  const [speedMultiplier, setSpeedMultiplier] = useState<number>(10);
  const [isRunning, setIsRunning] = useState<boolean>(false);
  const [result, setResult] = useState<SimulationResult | null>(null);
  const [error, setError] = useState<string>('');

  useEffect(() => {
    loadScenarios();
    loadFleetInfo();
  }, []);

  const loadScenarios = async () => {
    try {
      const data = await api.listScenarios();
      setScenarios(data.scenarios);
      if (data.scenarios.length > 0) {
        setSelectedScenario(data.scenarios[0].type);
      }
    } catch (err: any) {
      setError(err.error?.message || 'Failed to load scenarios');
    }
  };

  const loadFleetInfo = async () => {
    try {
      const data = await api.getFleetInfo();
      setFleetInfo(data);
    } catch (err: any) {
      console.error('Failed to load fleet info:', err);
    }
  };

  const runSimulation = async () => {
    if (!selectedScenario) {
      setError('Please select a scenario');
      return;
    }

    setIsRunning(true);
    setError('');
    setResult(null);

    try {
      const data = await api.runSimulation({
        scenario_type: selectedScenario,
        customer_count: customerCount,
        duration_seconds: duration,
        speed_multiplier: speedMultiplier,
        create_customers: true,
      });
      setResult(data);
    } catch (err: any) {
      setError(err.error?.message || 'Simulation failed');
    } finally {
      setIsRunning(false);
    }
  };

  const getScenarioName = (type: string) => {
    return scenarios.find(s => s.type === type)?.name || type;
  };

  const formatDuration = (seconds: number) => {
    if (seconds < 60) return `${seconds.toFixed(1)}s`;
    return `${(seconds / 60).toFixed(1)}m`;
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold">Fleet Simulation</h1>
        <p className="text-gray-600 mt-2">
          Test arbitration engine with simulated multi-agent scenarios
        </p>
      </div>

      {/* Fleet Info */}
      {fleetInfo && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Users className="h-5 w-5" />
              Agent Fleet
            </CardTitle>
            <CardDescription>
              {fleetInfo.fleet_stats.total_agents} autonomous agents ready for simulation
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {Object.entries(fleetInfo.agent_info).map(([type, info]) => (
                <div key={type} className="border rounded-lg p-4">
                  <h4 className="font-semibold text-sm mb-2">{info.name}</h4>
                  <p className="text-xs text-gray-600 mb-3">{info.description}</p>
                  <div className="space-y-1 text-xs">
                    <div className="flex justify-between">
                      <span className="text-gray-500">Priority:</span>
                      <span className="font-medium">{info.behavior.priority}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-500">Value:</span>
                      <span className="font-medium">{info.behavior.estimated_value}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-500">Urgency:</span>
                      <Badge variant="outline" className="text-xs">{info.behavior.urgency}</Badge>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Simulation Configuration */}
      <Card>
        <CardHeader>
          <CardTitle>Configure Simulation</CardTitle>
          <CardDescription>Select scenario and parameters</CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Scenario Selection */}
          <div>
            <label className="block text-sm font-medium mb-2">Scenario</label>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
              {scenarios.map((scenario) => (
                <button
                  key={scenario.type}
                  onClick={() => setSelectedScenario(scenario.type)}
                  className={`p-4 border-2 rounded-lg text-left transition-colors ${
                    selectedScenario === scenario.type
                      ? 'border-blue-500 bg-blue-50'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                  disabled={isRunning}
                >
                  <h4 className="font-semibold text-sm mb-1">{scenario.name}</h4>
                  <p className="text-xs text-gray-600">{scenario.description}</p>
                </button>
              ))}
            </div>
          </div>

          {/* Parameters */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium mb-2">
                Customers
              </label>
              <input
                type="number"
                value={customerCount}
                onChange={(e) => setCustomerCount(Number(e.target.value))}
                min={1}
                max={100}
                className="w-full px-3 py-2 border rounded-md"
                disabled={isRunning}
              />
              <p className="text-xs text-gray-500 mt-1">1-100 customers</p>
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">
                Duration (seconds)
              </label>
              <input
                type="number"
                value={duration}
                onChange={(e) => setDuration(Number(e.target.value))}
                min={60}
                max={3600}
                step={60}
                className="w-full px-3 py-2 border rounded-md"
                disabled={isRunning}
              />
              <p className="text-xs text-gray-500 mt-1">60-3600 seconds</p>
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">
                Speed Multiplier
              </label>
              <select
                value={speedMultiplier}
                onChange={(e) => setSpeedMultiplier(Number(e.target.value))}
                className="w-full px-3 py-2 border rounded-md"
                disabled={isRunning}
              >
                <option value={0.1}>0.1x (slower)</option>
                <option value={1}>1x (real-time)</option>
                <option value={5}>5x</option>
                <option value={10}>10x (recommended)</option>
                <option value={20}>20x</option>
                <option value={50}>50x</option>
                <option value={100}>100x (fastest)</option>
              </select>
              <p className="text-xs text-gray-500 mt-1">
                Actual: ~{formatDuration(duration / speedMultiplier)}
              </p>
            </div>
          </div>

          {/* Run Button */}
          <div className="flex items-center gap-4">
            <Button
              onClick={runSimulation}
              disabled={isRunning || !selectedScenario}
              className="flex items-center gap-2"
            >
              {isRunning ? (
                <>
                  <div className="animate-spin h-4 w-4 border-2 border-white border-t-transparent rounded-full" />
                  Running Simulation...
                </>
              ) : (
                <>
                  <Play className="h-4 w-4" />
                  Run Simulation
                </>
              )}
            </Button>

            {isRunning && (
              <span className="text-sm text-gray-600">
                Processing {customerCount} customers with {getScenarioName(selectedScenario)} scenario...
              </span>
            )}
          </div>

          {error && (
            <div className="flex items-center gap-2 text-red-600 bg-red-50 p-3 rounded-md">
              <AlertCircle className="h-4 w-4" />
              <span className="text-sm">{error}</span>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Results */}
      {result && (
        <>
          {/* Summary Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-600">Total Requests</p>
                    <p className="text-2xl font-bold">{result.total_requests}</p>
                  </div>
                  <Zap className="h-8 w-8 text-blue-500" />
                </div>
                <p className="text-xs text-gray-500 mt-2">
                  {result.metrics.requests_per_second.toFixed(2)} req/s
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-600">Allow Rate</p>
                    <p className="text-2xl font-bold text-green-600">
                      {(result.metrics.allow_rate * 100).toFixed(1)}%
                    </p>
                  </div>
                  <TrendingUp className="h-8 w-8 text-green-500" />
                </div>
                <p className="text-xs text-gray-500 mt-2">
                  {result.results.allow} allowed
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-600">Block Rate</p>
                    <p className="text-2xl font-bold text-red-600">
                      {(result.metrics.block_rate * 100).toFixed(1)}%
                    </p>
                  </div>
                  <AlertCircle className="h-8 w-8 text-red-500" />
                </div>
                <p className="text-xs text-gray-500 mt-2">
                  {result.results.block} blocked
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-600">Duration</p>
                    <p className="text-2xl font-bold">
                      {formatDuration(result.duration_seconds)}
                    </p>
                  </div>
                  <Clock className="h-8 w-8 text-purple-500" />
                </div>
                <p className="text-xs text-gray-500 mt-2">
                  {result.metrics.speedup.toFixed(1)}x speedup
                </p>
              </CardContent>
            </Card>
          </div>

          {/* Detailed Results */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Decision Breakdown */}
            <Card>
              <CardHeader>
                <CardTitle>Decision Breakdown</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-sm">Allowed</span>
                    <div className="flex items-center gap-2">
                      <div className="w-48 h-2 bg-gray-200 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-green-500"
                          style={{ width: `${result.metrics.allow_rate * 100}%` }}
                        />
                      </div>
                      <span className="text-sm font-medium w-16 text-right">
                        {result.results.allow}
                      </span>
                    </div>
                  </div>

                  <div className="flex items-center justify-between">
                    <span className="text-sm">Blocked</span>
                    <div className="flex items-center gap-2">
                      <div className="w-48 h-2 bg-gray-200 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-red-500"
                          style={{ width: `${result.metrics.block_rate * 100}%` }}
                        />
                      </div>
                      <span className="text-sm font-medium w-16 text-right">
                        {result.results.block}
                      </span>
                    </div>
                  </div>

                  <div className="flex items-center justify-between">
                    <span className="text-sm">Delayed</span>
                    <div className="flex items-center gap-2">
                      <div className="w-48 h-2 bg-gray-200 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-yellow-500"
                          style={{ width: `${result.metrics.delay_rate * 100}%` }}
                        />
                      </div>
                      <span className="text-sm font-medium w-16 text-right">
                        {result.results.delay}
                      </span>
                    </div>
                  </div>

                  <div className="flex items-center justify-between">
                    <span className="text-sm">Merged</span>
                    <div className="flex items-center gap-2">
                      <div className="w-48 h-2 bg-gray-200 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-blue-500"
                          style={{ width: `${result.metrics.merge_rate * 100}%` }}
                        />
                      </div>
                      <span className="text-sm font-medium w-16 text-right">
                        {result.results.merge}
                      </span>
                    </div>
                  </div>

                  {result.results.errors > 0 && (
                    <div className="flex items-center justify-between">
                      <span className="text-sm">Errors</span>
                      <div className="flex items-center gap-2">
                        <div className="w-48 h-2 bg-gray-200 rounded-full overflow-hidden">
                          <div
                            className="h-full bg-gray-500"
                            style={{ width: `${result.metrics.error_rate * 100}%` }}
                          />
                        </div>
                        <span className="text-sm font-medium w-16 text-right">
                          {result.results.errors}
                        </span>
                      </div>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>

            {/* By Agent Type */}
            <Card>
              <CardHeader>
                <CardTitle>Requests by Agent</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {Object.entries(result.results.by_agent)
                    .sort(([, a], [, b]) => b - a)
                    .map(([agent, count]) => (
                      <div key={agent} className="flex items-center justify-between">
                        <span className="text-sm">{agent}</span>
                        <div className="flex items-center gap-2">
                          <div className="w-48 h-2 bg-gray-200 rounded-full overflow-hidden">
                            <div
                              className="h-full bg-blue-500"
                              style={{
                                width: `${(count / result.total_requests) * 100}%`,
                              }}
                            />
                          </div>
                          <span className="text-sm font-medium w-16 text-right">
                            {count}
                          </span>
                        </div>
                      </div>
                    ))}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Sample Decisions */}
          {result.results.decisions.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>Sample Decisions</CardTitle>
                <CardDescription>First 20 decisions from simulation</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead className="border-b">
                      <tr className="text-left">
                        <th className="pb-2 font-medium">Request ID</th>
                        <th className="pb-2 font-medium">Customer</th>
                        <th className="pb-2 font-medium">Intent</th>
                        <th className="pb-2 font-medium">Decision</th>
                        <th className="pb-2 font-medium text-right">Score</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y">
                      {result.results.decisions.map((decision, idx) => (
                        <tr key={idx}>
                          <td className="py-2 font-mono text-xs">
                            {decision.request_id.substring(0, 20)}...
                          </td>
                          <td className="py-2 text-xs">{decision.customer_id}</td>
                          <td className="py-2">
                            <Badge variant="outline" className="text-xs">
                              {decision.intent}
                            </Badge>
                          </td>
                          <td className="py-2">
                            <Badge
                              variant={
                                decision.decision === 'ALLOW'
                                  ? 'default'
                                  : decision.decision === 'BLOCK'
                                  ? 'destructive'
                                  : 'secondary'
                              }
                              className="text-xs"
                            >
                              {decision.decision}
                            </Badge>
                          </td>
                          <td className="py-2 text-right font-medium">
                            {decision.score.toFixed(1)}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>
          )}
        </>
      )}
    </div>
  );
}
