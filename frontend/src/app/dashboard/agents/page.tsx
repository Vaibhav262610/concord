'use client';

import React, { useEffect, useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { api, type Agent } from '@/lib/api';
import { formatDate, copyToClipboard } from '@/lib/utils';
import { Plus, Copy, Check, Eye, EyeOff, Loader2, CheckCircle2, XCircle } from 'lucide-react';

export default function AgentsPage() {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [visibleApiKeys, setVisibleApiKeys] = useState<Set<string>>(new Set());
  const [copiedKey, setCopiedKey] = useState<string | null>(null);

  useEffect(() => {
    loadAgents();
  }, []);

  async function loadAgents() {
    try {
      const data = await api.listAgents({ limit: 100 });
      setAgents(data.agents);
    } catch (error) {
      console.error('Failed to load agents:', error);
    } finally {
      setLoading(false);
    }
  }

  async function handleCreateAgent(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const formData = new FormData(event.currentTarget);

    try {
      const newAgent = await api.createAgent({
        name: formData.get('name') as string,
        agent_type: formData.get('agent_type') as string,
        description: formData.get('description') as string,
        permissions: {
          messaging: formData.get('messaging') === 'on',
          discounts: formData.get('discounts') === 'on',
          high_value_discounts: formData.get('high_value_discounts') === 'on',
        },
      });

      setAgents([newAgent, ...agents]);
      setShowCreateForm(false);
      
      // Show the API key temporarily
      if (newAgent.api_key) {
        setVisibleApiKeys(new Set([newAgent.id]));
      }
    } catch (error) {
      console.error('Failed to create agent:', error);
      alert('Failed to create agent. Please try again.');
    }
  }

  function toggleApiKeyVisibility(agentId: string) {
    setVisibleApiKeys((prev) => {
      const next = new Set(prev);
      if (next.has(agentId)) {
        next.delete(agentId);
      } else {
        next.add(agentId);
      }
      return next;
    });
  }

  async function handleCopyApiKey(agentId: string, apiKey: string) {
    const success = await copyToClipboard(apiKey);
    if (success) {
      setCopiedKey(agentId);
      setTimeout(() => setCopiedKey(null), 2000);
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
          <h1 className="text-3xl font-bold text-gray-900">Agent Management</h1>
          <p className="mt-2 text-gray-600">
            Manage your autonomous agent fleet
          </p>
        </div>
        <Button onClick={() => setShowCreateForm(!showCreateForm)}>
          <Plus className="w-4 h-4 mr-2" />
          Create Agent
        </Button>
      </div>

      {/* Create Form */}
      {showCreateForm && (
        <Card>
          <CardHeader>
            <CardTitle>Create New Agent</CardTitle>
            <CardDescription>Register a new autonomous agent</CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleCreateAgent} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Agent Name *
                </label>
                <input
                  type="text"
                  name="name"
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="e.g., Payment Recovery Bot"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Agent Type *
                </label>
                <input
                  type="text"
                  name="agent_type"
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="e.g., payment_recovery, marketing, support"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Description
                </label>
                <textarea
                  name="description"
                  rows={3}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="Brief description of the agent's purpose"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Permissions
                </label>
                <div className="space-y-2">
                  <label className="flex items-center">
                    <input type="checkbox" name="messaging" className="mr-2" defaultChecked />
                    <span className="text-sm">Messaging</span>
                  </label>
                  <label className="flex items-center">
                    <input type="checkbox" name="discounts" className="mr-2" defaultChecked />
                    <span className="text-sm">Discounts</span>
                  </label>
                  <label className="flex items-center">
                    <input type="checkbox" name="high_value_discounts" className="mr-2" />
                    <span className="text-sm">High Value Discounts</span>
                  </label>
                </div>
              </div>

              <div className="flex space-x-3">
                <Button type="submit">Create Agent</Button>
                <Button type="button" variant="outline" onClick={() => setShowCreateForm(false)}>
                  Cancel
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      )}

      {/* Agents List */}
      <div className="grid gap-6">
        {agents.length === 0 ? (
          <Card>
            <CardContent className="py-12 text-center">
              <p className="text-gray-500">No agents registered yet. Create your first agent above.</p>
            </CardContent>
          </Card>
        ) : (
          agents.map((agent) => (
            <Card key={agent.id}>
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div>
                    <CardTitle className="flex items-center space-x-2">
                      <span>{agent.name}</span>
                      {agent.is_active ? (
                        <Badge variant="success">Active</Badge>
                      ) : (
                        <Badge variant="destructive">Inactive</Badge>
                      )}
                    </CardTitle>
                    <CardDescription className="mt-1">
                      <span className="inline-block px-2 py-0.5 text-xs bg-gray-100 rounded">
                        {agent.agent_type}
                      </span>
                    </CardDescription>
                  </div>
                  <div className="text-sm text-gray-500">
                    Created {formatDate(agent.created_at)}
                  </div>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                {agent.description && (
                  <p className="text-sm text-gray-600">{agent.description}</p>
                )}

                <div>
                  <h4 className="text-sm font-medium text-gray-700 mb-2">Permissions</h4>
                  <div className="flex flex-wrap gap-2">
                    {agent.permissions.messaging && (
                      <Badge variant="info">
                        <CheckCircle2 className="w-3 h-3 mr-1" />
                        Messaging
                      </Badge>
                    )}
                    {agent.permissions.discounts && (
                      <Badge variant="info">
                        <CheckCircle2 className="w-3 h-3 mr-1" />
                        Discounts
                      </Badge>
                    )}
                    {agent.permissions.high_value_discounts && (
                      <Badge variant="warning">
                        <CheckCircle2 className="w-3 h-3 mr-1" />
                        High Value Discounts
                      </Badge>
                    )}
                  </div>
                </div>

                {agent.api_key && (
                  <div>
                    <h4 className="text-sm font-medium text-gray-700 mb-2">API Key</h4>
                    <div className="flex items-center space-x-2">
                      <code className="flex-1 px-3 py-2 bg-gray-50 border border-gray-200 rounded text-sm font-mono">
                        {visibleApiKeys.has(agent.id) ? agent.api_key : '••••••••••••••••••••••••••••••••'}
                      </code>
                      <Button
                        variant="outline"
                        size="icon"
                        onClick={() => toggleApiKeyVisibility(agent.id)}
                      >
                        {visibleApiKeys.has(agent.id) ? (
                          <EyeOff className="w-4 h-4" />
                        ) : (
                          <Eye className="w-4 h-4" />
                        )}
                      </Button>
                      <Button
                        variant="outline"
                        size="icon"
                        onClick={() => handleCopyApiKey(agent.id, agent.api_key!)}
                      >
                        {copiedKey === agent.id ? (
                          <Check className="w-4 h-4 text-green-500" />
                        ) : (
                          <Copy className="w-4 h-4" />
                        )}
                      </Button>
                    </div>
                    <p className="text-xs text-gray-500 mt-1">
                      ⚠️ Keep this key secure. It cannot be retrieved later.
                    </p>
                  </div>
                )}
              </CardContent>
            </Card>
          ))
        )}
      </div>
    </div>
  );
}
