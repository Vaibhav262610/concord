"use client";

import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { api, Customer, CustomerStats, CustomerAnalytics } from '@/lib/api';
import { Users, TrendingUp, UserX, Search, Plus, Eye, Trash2, Edit, BarChart, Mail, Phone } from 'lucide-react';

export default function CustomersPage() {
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [stats, setStats] = useState<CustomerStats | null>(null);
  const [selectedCustomer, setSelectedCustomer] = useState<Customer | null>(null);
  const [analytics, setAnalytics] = useState<CustomerAnalytics | null>(null);
  const [total, setTotal] = useState<number>(0);
  const [page, setPage] = useState<number>(0);
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [showCreateModal, setShowCreateModal] = useState<boolean>(false);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string>('');

  const pageSize = 20;

  useEffect(() => {
    loadCustomers();
    loadStats();
  }, [page, searchQuery]);

  const loadCustomers = async () => {
    setLoading(true);
    setError('');
    try {
      const data = await api.listCustomers({
        skip: page * pageSize,
        limit: pageSize,
        search: searchQuery || undefined
      });
      setCustomers(data.customers);
      setTotal(data.total);
    } catch (err: any) {
      setError(err.error?.message || 'Failed to load customers');
    } finally {
      setLoading(false);
    }
  };

  const loadStats = async () => {
    try {
      const data = await api.getCustomerStats();
      setStats(data);
    } catch (err: any) {
      console.error('Failed to load stats:', err);
    }
  };

  const viewCustomerAnalytics = async (customer: Customer) => {
    setSelectedCustomer(customer);
    setAnalytics(null);
    try {
      const data = await api.getCustomerAnalytics(customer.id, 30);
      setAnalytics(data);
    } catch (err: any) {
      console.error('Failed to load analytics:', err);
    }
  };

  const handleSearch = () => {
    setPage(0);
    loadCustomers();
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const totalPages = Math.ceil(total / pageSize);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Customer Management</h1>
          <p className="text-gray-600 mt-2">
            Manage customer profiles, consent, and analytics
          </p>
        </div>
        <Button onClick={() => setShowCreateModal(true)} className="flex items-center gap-2">
          <Plus className="h-4 w-4" />
          Add Customer
        </Button>
      </div>

      {/* Stats Cards */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">Total Customers</p>
                  <p className="text-2xl font-bold">{stats.total_customers}</p>
                </div>
                <Users className="h-8 w-8 text-blue-500" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">Active (30d)</p>
                  <p className="text-2xl font-bold text-green-600">{stats.active_customers}</p>
                </div>
                <TrendingUp className="h-8 w-8 text-green-500" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">Opted Out</p>
                  <p className="text-2xl font-bold text-red-600">{stats.opted_out}</p>
                </div>
                <UserX className="h-8 w-8 text-red-500" />
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Customers List */}
        <div className="lg:col-span-2">
          <Card>
            <CardHeader>
              <CardTitle>Customers</CardTitle>
              <CardDescription>
                {total} total customer{total !== 1 ? 's' : ''}
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Search */}
              <div className="flex gap-2">
                <div className="relative flex-1">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                  <input
                    type="text"
                    placeholder="Search by name, email, or ID..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
                    className="w-full pl-10 pr-4 py-2 border rounded-md"
                  />
                </div>
                <Button onClick={handleSearch} variant="outline">
                  Search
                </Button>
              </div>

              {/* Loading/Error */}
              {loading && (
                <div className="text-center py-8 text-gray-500">Loading customers...</div>
              )}
              {error && (
                <div className="text-center py-8 text-red-600">{error}</div>
              )}

              {/* Customer List */}
              {!loading && !error && customers.length === 0 && (
                <div className="text-center py-8 text-gray-500">
                  No customers found. Create your first customer to get started.
                </div>
              )}

              {!loading && !error && customers.length > 0 && (
                <div className="space-y-2">
                  {customers.map((customer) => (
                    <div
                      key={customer.id}
                      className={`p-4 border rounded-lg transition-colors cursor-pointer ${
                        selectedCustomer?.id === customer.id
                          ? 'border-blue-500 bg-blue-50'
                          : 'hover:border-gray-300'
                      }`}
                      onClick={() => viewCustomerAnalytics(customer)}
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-1">
                            <h4 className="font-semibold">
                              {customer.name || customer.external_id}
                            </h4>
                            {customer.consent?.global_opt_out && (
                              <Badge variant="destructive" className="text-xs">Opted Out</Badge>
                            )}
                          </div>
                          <p className="text-sm text-gray-600 mb-2">ID: {customer.external_id}</p>
                          <div className="flex flex-wrap gap-3 text-xs text-gray-500">
                            {customer.email && (
                              <span className="flex items-center gap-1">
                                <Mail className="h-3 w-3" />
                                {customer.email}
                              </span>
                            )}
                            {customer.phone && (
                              <span className="flex items-center gap-1">
                                <Phone className="h-3 w-3" />
                                {customer.phone}
                              </span>
                            )}
                          </div>
                        </div>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={(e) => {
                            e.stopPropagation();
                            viewCustomerAnalytics(customer);
                          }}
                        >
                          <Eye className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {/* Pagination */}
              {totalPages > 1 && (
                <div className="flex items-center justify-between pt-4 border-t">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setPage(Math.max(0, page - 1))}
                    disabled={page === 0}
                  >
                    Previous
                  </Button>
                  <span className="text-sm text-gray-600">
                    Page {page + 1} of {totalPages}
                  </span>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setPage(Math.min(totalPages - 1, page + 1))}
                    disabled={page >= totalPages - 1}
                  >
                    Next
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Customer Analytics Panel */}
        <div className="lg:col-span-1">
          {!selectedCustomer && (
            <Card>
              <CardContent className="pt-6">
                <div className="text-center py-8 text-gray-500">
                  <BarChart className="h-12 w-12 mx-auto mb-3 opacity-50" />
                  <p>Select a customer to view analytics</p>
                </div>
              </CardContent>
            </Card>
          )}

          {selectedCustomer && !analytics && (
            <Card>
              <CardContent className="pt-6">
                <div className="text-center py-8 text-gray-500">
                  Loading analytics...
                </div>
              </CardContent>
            </Card>
          )}

          {selectedCustomer && analytics && (
            <div className="space-y-4">
              {/* Customer Info Card */}
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">{selectedCustomer.name || 'Customer'}</CardTitle>
                  <CardDescription>{selectedCustomer.external_id}</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div>
                    <p className="text-sm text-gray-600 mb-2">Contact</p>
                    <div className="space-y-1 text-sm">
                      {selectedCustomer.email && (
                        <div className="flex items-center gap-2">
                          <Mail className="h-3 w-3 text-gray-400" />
                          {selectedCustomer.email}
                        </div>
                      )}
                      {selectedCustomer.phone && (
                        <div className="flex items-center gap-2">
                          <Phone className="h-3 w-3 text-gray-400" />
                          {selectedCustomer.phone}
                        </div>
                      )}
                    </div>
                  </div>

                  <div>
                    <p className="text-sm text-gray-600 mb-2">Consent</p>
                    <div className="flex flex-wrap gap-2">
                      <Badge variant={selectedCustomer.consent?.marketing ? 'default' : 'secondary'}>
                        Marketing: {selectedCustomer.consent?.marketing ? 'Yes' : 'No'}
                      </Badge>
                      <Badge variant={selectedCustomer.consent?.transactional ? 'default' : 'secondary'}>
                        Transactional: {selectedCustomer.consent?.transactional ? 'Yes' : 'No'}
                      </Badge>
                    </div>
                  </div>

                  <div className="pt-4 border-t">
                    <p className="text-xs text-gray-500">
                      Created {formatDate(selectedCustomer.created_at)}
                    </p>
                  </div>
                </CardContent>
              </Card>

              {/* Analytics Card */}
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">Analytics (30 days)</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm text-gray-600">Total Requests</span>
                      <span className="font-bold">{analytics.total_requests}</span>
                    </div>
                    {analytics.last_contact_at && (
                      <p className="text-xs text-gray-500">
                        Last contact: {formatDate(analytics.last_contact_at)}
                      </p>
                    )}
                  </div>

                  {Object.keys(analytics.requests_by_intent).length > 0 && (
                    <div>
                      <p className="text-sm text-gray-600 mb-2">By Intent</p>
                      <div className="space-y-1">
                        {Object.entries(analytics.requests_by_intent)
                          .sort(([, a], [, b]) => b - a)
                          .map(([intent, count]) => (
                            <div key={intent} className="flex justify-between text-sm">
                              <span>{intent}</span>
                              <span className="font-medium">{count}</span>
                            </div>
                          ))}
                      </div>
                    </div>
                  )}

                  {Object.keys(analytics.decisions).length > 0 && (
                    <div>
                      <p className="text-sm text-gray-600 mb-2">Decisions</p>
                      <div className="space-y-1">
                        {Object.entries(analytics.decisions).map(([decision, count]) => (
                          <div key={decision} className="flex justify-between text-sm">
                            <Badge
                              variant={
                                decision === 'allow'
                                  ? 'default'
                                  : decision === 'block'
                                  ? 'destructive'
                                  : 'secondary'
                              }
                              className="text-xs"
                            >
                              {decision}
                            </Badge>
                            <span className="font-medium">{count}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  <div className="pt-4 border-t">
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600">Total Value</span>
                      <span className="font-bold">
                        ₹{(analytics.total_value_engaged / 100).toFixed(2)}
                      </span>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}
        </div>
      </div>

      {/* Create Modal (placeholder - would need full implementation) */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <Card className="w-full max-w-md">
            <CardHeader>
              <CardTitle>Add Customer</CardTitle>
              <CardDescription>Create a new customer profile</CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-gray-600">
                Customer creation form would go here. For now, use the API directly or simulation.
              </p>
              <div className="flex gap-2 mt-4">
                <Button variant="outline" onClick={() => setShowCreateModal(false)} className="flex-1">
                  Cancel
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
