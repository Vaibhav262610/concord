import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { ArrowRight, CheckCircle2 } from 'lucide-react';

export default function Home() {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center p-8 bg-gradient-to-br from-blue-50 via-white to-purple-50">
      <div className="text-center space-y-8 max-w-4xl">
        <div className="space-y-4">
          <div className="inline-block px-4 py-2 bg-blue-100 text-blue-700 rounded-full text-sm font-semibold mb-4">
            🚀 Razorpay AI Buildathon 2026
          </div>
          <h1 className="text-6xl font-bold tracking-tight bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
            CONCORD
          </h1>
          <p className="text-2xl text-gray-600 max-w-2xl mx-auto">
            The customer-level control plane for autonomous agent fleets
          </p>
        </div>

        <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
          <Link href="/dashboard">
            <Button size="lg" className="text-lg px-8 py-6">
              Open Dashboard
              <ArrowRight className="ml-2 w-5 h-5" />
            </Button>
          </Link>
          <a href="http://localhost:8000/docs" target="_blank" rel="noopener noreferrer">
            <Button size="lg" variant="outline" className="text-lg px-8 py-6">
              API Documentation
            </Button>
          </a>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-12 text-left">
          <div className="bg-white rounded-lg p-6 shadow-sm border border-gray-200">
            <h3 className="font-semibold text-lg mb-3 flex items-center">
              <CheckCircle2 className="w-5 h-5 text-green-500 mr-2" />
              Complete Backend MVP
            </h3>
            <ul className="space-y-2 text-sm text-gray-600">
              <li>✓ Agent Gateway with authentication</li>
              <li>✓ 13-step Arbitration Engine</li>
              <li>✓ Multi-channel Execution Layer</li>
              <li>✓ Delivery Tracking & Webhooks</li>
            </ul>
          </div>

          <div className="bg-white rounded-lg p-6 shadow-sm border border-gray-200">
            <h3 className="font-semibold text-lg mb-3 flex items-center">
              <CheckCircle2 className="w-5 h-5 text-green-500 mr-2" />
              Production-Ready Dashboard
            </h3>
            <ul className="space-y-2 text-sm text-gray-600">
              <li>✓ Real-time monitoring</li>
              <li>✓ Agent fleet management</li>
              <li>✓ Decision analytics</li>
              <li>✓ Delivery metrics & charts</li>
            </ul>
          </div>
        </div>

        <div className="pt-8 text-sm text-gray-500">
          <p>All 4 Backend Phases Complete • 21/21 Tests Passing (100%)</p>
        </div>
      </div>
    </div>
  );
}
