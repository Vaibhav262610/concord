'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { api, type ActionResponse, type Agent } from '@/lib/api';
import { generateRequestId, getDecisionColor, formatDate, getChannelIcon } from '@/lib/utils';
import { Send, CheckCircle2, XCircle, Clock, AlertCircle } from 'lucide-react';

export default function ActionsPage() {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [selectedAgent, setSelectedAgent] = useState<string>('');
  const [submitting, setSubmitting] = useState(false);
  const [response, setResponse] = useState<ActionResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadAgents();
  }, []);

  async function loadAgents() {
    try {
      const data = await api.listAgents({ limit: 100 });
      setAgents(data.agents.filter(a => a.is_active));
      if (data.agents.length > 0 && data.agents[0].api_key) {
        setSelectedAgent(data.agents[0].id);
        api.setAuthToken(data.agents[0].api_key);
      }
    } catch (error) {
      console.error('Failed to load agents:', error);
    }
  }

  function handleAgentChange(agentId: string) {
    setSelectedAgent(agentId);
    const agent = agents.find(a => a.id === agentId);
    if (agent?.api_key) {
      api.setAuthToken(agent.api_key);
    }
  }

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitting(true);
    setResponse(null);
    setError(null);

    const formData = new FormData(event.currentTarget);

    try {
      const actionData: any = {
        request_id: generateRequestId(),
        customer_id: formData.get('customer_id') as string,
        action: formData.get('action') as string,
        intent: formData.get('intent') as string,
        channel: formData.get('channel') as string,
        priority: parseInt(formData.get('priority') as string) || undefined,
        estimated_value: parseInt(formData.get('estimated_value') as string) || undefined,
        urgency: formData.get('urgency') as string || undefined,
        message: formData.get('message') as string || undefined,
      };

      // Add offer if discount fields are filled
      const discountType = formData.get('discount_type') as string;
      const discountValue = formData.get('discount_value') as string;
      if (discountType && discountValue) {
        actionData.offer = {
          discount_type: discountType,
          discount_value: parseInt(discountValue),
        };
      }

      const result = await api.submitAction(actionData);
      setResponse(result);
    } catch (err: any) {
      setError(err.error?.message || 'Failed to submit action request');
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="space-y-6 max-w-4xl">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Submit Action Request</h1>
        <p className="mt-2 text-gray-600">
          Test the complete arbitration → execution flow
        </p>
      </div>

      {/* Agent Selection */}
      {agents.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Select Agent</CardTitle>
            <CardDescription>Choose which agent will submit this request</CardDescription>
          </CardHeader>
          <CardContent>
            <select
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              value={selectedAgent}
              onChange={(e) => handleAgentChange(e.target.value)}
            >
              {agents.map((agent) => (
                <option key={agent.id} value={agent.id}>
                  {agent.name} ({agent.agent_type})
                </option>
              ))}
            </select>
          </CardContent>
        </Card>
      )}

      {/* Action Form */}
      <Card>
        <CardHeader>
          <CardTitle>Action Details</CardTitle>
          <CardDescription>Fill in the action request parameters</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Basic Fields */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Customer ID *
                </label>
                <input
                  type="text"
                  name="customer_id"
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="e.g., CUST_001"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Action *
                </label>
                <select
                  name="action"
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="SEND_MESSAGE">SEND_MESSAGE</option>
                  <option value="SEND_OFFER">SEND_OFFER</option>
                  <option value="SEND_REMINDER">SEND_REMINDER</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Intent *
                </label>
                <select
                  name="intent"
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="PAYMENT_RECOVERY">PAYMENT_RECOVERY</option>
                  <option value="MARKETING">MARKETING</option>
                  <option value="TRANSACTIONAL">TRANSACTIONAL</option>
                  <option value="SUPPORT">SUPPORT</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Channel *
                </label>
                <select
                  name="channel"
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="EMAIL">📧 EMAIL</option>
                  <option value="SMS">💬 SMS</option>
                  <option value="WHATSAPP">💚 WHATSAPP</option>
                  <option value="PUSH">🔔 PUSH</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Priority (0-100)
                </label>
                <input
                  type="number"
                  name="priority"
                  min="0"
                  max="100"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="e.g., 85"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Estimated Value (paise)
                </label>
                <input
                  type="number"
                  name="estimated_value"
                  min="0"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="e.g., 500000 (₹5,000)"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Urgency
                </label>
                <select
                  name="urgency"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">Select urgency</option>
                  <option value="HIGH">HIGH</option>
                  <option value="MEDIUM">MEDIUM</option>
                  <option value="LOW">LOW</option>
                </select>
              </div>
            </div>

            {/* Message */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Message
              </label>
              <textarea
                name="message"
                rows={3}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Optional message content"
              />
            </div>

            {/* Offer (Optional) */}
            <div className="border-t border-gray-200 pt-4">
              <h3 className="text-sm font-semibold text-gray-700 mb-3">Offer (Optional)</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Discount Type
                  </label>
                  <select
                    name="discount_type"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="">No discount</option>
                    <option value="PERCENTAGE">PERCENTAGE</option>
                    <option value="FIXED">FIXED</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Discount Value
                  </label>
                  <input
                    type="number"
                    name="discount_value"
                    min="0"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="e.g., 10 (for 10% or ₹0.10)"
                  />
                </div>
              </div>
            </div>

            {/* Submit Button */}
            <div className="flex space-x-3 pt-4">
              <Button type="submit" disabled={submitting || agents.length === 0}>
                {submitting ? (
                  <>
                    <Clock className="w-4 h-4 mr-2 animate-spin" />
                    Submitting...
                  </>
                ) : (
                  <>
                    <Send className="w-4 h-4 mr-2" />
                    Submit Action
                  </>
                )}
              </Button>
              <Button
                type="button"
                variant="outline"
                onClick={() => {
                  setResponse(null);
                  setError(null);
                }}
              >
                Clear Result
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>

      {/* Error Display */}
      {error && (
        <Card className="border-red-200 bg-red-50">
          <CardContent className="py-6">
            <div className="flex items-start space-x-3">
              <XCircle className="w-6 h-6 text-red-600 flex-shrink-0 mt-0.5" />
              <div>
                <h3 className="text-lg font-semibold text-red-900">Request Failed</h3>
                <p className="text-sm text-red-700 mt-1">{error}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Success Response */}
      {response && (
        <div className="space-y-4">
          <Card className="border-green-200 bg-green-50">
            <CardContent className="py-6">
              <div className="flex items-start space-x-3">
                <CheckCircle2 className="w-6 h-6 text-green-600 flex-shrink-0 mt-0.5" />
                <div className="flex-1">
                  <h3 className="text-lg font-semibold text-green-900">Request Submitted Successfully!</h3>
                  <p className="text-sm text-green-700 mt-1">
                    The arbitration engine has processed your request.
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Decision Details */}
          <Card>
            <CardHeader>
              <CardTitle>Arbitration Decision</CardTitle>
              <CardDescription>Result from the 13-step decision engine</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <Badge className={getDecisionColor(response.decision.decision_type)} style={{ fontSize: '1rem', padding: '0.5rem 1rem' }}>
                    {response.decision.decision_type}
                  </Badge>
                  <span className="text-lg font-semibold">
                    Score: {response.decision.final_score.toFixed(1)}/100
                  </span>
                </div>
                <span className="text-2xl">{getChannelIcon(response.request.channel)}</span>
              </div>

              <div className="bg-gray-50 rounded-lg p-4">
                <p className="text-sm font-medium text-gray-700 mb-1">Reason</p>
                <p className="text-gray-900">{response.decision.decision_reason}</p>
                {response.decision.delay_reason && (
                  <p className="text-yellow-700 mt-2">
                    ⏱️ Delay: {response.decision.delay_reason}
                  </p>
                )}
              </div>

              {/* Score Breakdown */}
              <div>
                <h4 className="text-sm font-semibold text-gray-700 mb-3">Score Breakdown</h4>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                  <div className="bg-blue-50 rounded p-3">
                    <p className="text-xs text-blue-600 font-medium">Priority</p>
                    <p className="text-lg font-bold text-blue-900">
                      {response.decision.scores.priority_score.toFixed(1)}
                    </p>
                  </div>
                  <div className="bg-green-50 rounded p-3">
                    <p className="text-xs text-green-600 font-medium">Value</p>
                    <p className="text-lg font-bold text-green-900">
                      {response.decision.scores.value_score.toFixed(1)}
                    </p>
                  </div>
                  <div className="bg-purple-50 rounded p-3">
                    <p className="text-xs text-purple-600 font-medium">Consent</p>
                    <p className="text-lg font-bold text-purple-900">
                      {response.decision.scores.consent_score.toFixed(1)}
                    </p>
                  </div>
                  <div className="bg-orange-50 rounded p-3">
                    <p className="text-xs text-orange-600 font-medium">Frequency</p>
                    <p className="text-lg font-bold text-orange-900">
                      {response.decision.scores.frequency_score.toFixed(1)}
                    </p>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Execution Details */}
          {response.execution && (
            <Card>
              <CardHeader>
                <CardTitle>Execution Result</CardTitle>
                <CardDescription>Message delivery status</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex items-center space-x-3 mb-3">
                  {response.execution.success ? (
                    <CheckCircle2 className="w-6 h-6 text-green-500" />
                  ) : (
                    <AlertCircle className="w-6 h-6 text-yellow-500" />
                  )}
                  <div>
                    <p className="font-semibold">{response.execution.message}</p>
                    <Badge className={`mt-1 ${response.execution.status === 'sent' ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'}`}>
                      {response.execution.status}
                    </Badge>
                  </div>
                </div>
                <p className="text-xs text-gray-500">
                  Execution ID: <code className="bg-gray-100 px-2 py-0.5 rounded">{response.execution.execution_id}</code>
                </p>
              </CardContent>
            </Card>
          )}

          {/* Request Details */}
          <Card>
            <CardHeader>
              <CardTitle>Request Details</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <p className="text-gray-500">Request ID</p>
                  <code className="text-xs bg-gray-100 px-2 py-0.5 rounded">{response.request.request_id}</code>
                </div>
                <div>
                  <p className="text-gray-500">Customer ID</p>
                  <p className="font-medium">{response.request.customer_id}</p>
                </div>
                <div>
                  <p className="text-gray-500">Duplicate</p>
                  <p className="font-medium">{response.is_duplicate ? 'Yes' : 'No'}</p>
                </div>
                <div>
                  <p className="text-gray-500">Created</p>
                  <p className="font-medium">{formatDate(response.decision.created_at)}</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
