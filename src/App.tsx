import React, { useState } from 'react';
import { Wallet2, DollarSign, Send } from 'lucide-react';
import toast, { Toaster } from 'react-hot-toast';
import { supabase } from './lib/supabase';

interface OrderForm {
  walletAddress: string;
  amount: string;
  email: string;
}

function App() {
  const [formData, setFormData] = useState<OrderForm>({
    walletAddress: '',
    amount: '',
    email: '',
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    try {
      // First, save to Supabase
      const { error: supabaseError } = await supabase
        .from('orders')
        .insert([
          {
            wallet_address: formData.walletAddress,
            amount: parseFloat(formData.amount),
            email: formData.email,
            status: 'pending'
          }
        ]);

      if (supabaseError) throw supabaseError;

      // Then, send to Python backend
      const response = await fetch('http://localhost:8000', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          wallet_address: formData.walletAddress,
          amount: formData.amount,
          email: formData.email,
        }),
      });

      const data = await response.json();
      
      if (!response.ok) throw new Error(data.message);

      toast.success('Order submitted successfully!');
      setFormData({ walletAddress: '', amount: '', email: '' });
    } catch (error) {
      toast.error('Failed to submit order. Please try again.');
      console.error('Error:', error);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-900 to-black text-white">
      <Toaster position="top-right" />
      
      <div className="container mx-auto px-4 py-12">
        <div className="max-w-2xl mx-auto">
          <div className="text-center mb-12">
            <div className="flex justify-center mb-4">
              <DollarSign className="w-16 h-16 text-blue-400" />
            </div>
            <h1 className="text-4xl font-bold mb-4">USDT Order System</h1>
            <p className="text-gray-300">Place your USDT order securely and efficiently</p>
          </div>

          <div className="bg-white/10 backdrop-blur-lg rounded-xl p-8 shadow-2xl">
            <form onSubmit={handleSubmit} className="space-y-6">
              <div>
                <label className="block text-sm font-medium mb-2">
                  <div className="flex items-center gap-2">
                    <Wallet2 className="w-4 h-4" />
                    Wallet Address
                  </div>
                </label>
                <input
                  type="text"
                  value={formData.walletAddress}
                  onChange={(e) => setFormData({ ...formData, walletAddress: e.target.value })}
                  className="w-full px-4 py-2 rounded-lg bg-white/5 border border-gray-600 focus:border-blue-400 focus:ring-1 focus:ring-blue-400 text-white"
                  placeholder="Enter your USDT wallet address"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">
                  <div className="flex items-center gap-2">
                    <DollarSign className="w-4 h-4" />
                    Amount (USDT)
                  </div>
                </label>
                <input
                  type="number"
                  value={formData.amount}
                  onChange={(e) => setFormData({ ...formData, amount: e.target.value })}
                  className="w-full px-4 py-2 rounded-lg bg-white/5 border border-gray-600 focus:border-blue-400 focus:ring-1 focus:ring-blue-400 text-white"
                  placeholder="Enter amount in USDT"
                  step="0.01"
                  min="0"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">Email Address</label>
                <input
                  type="email"
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  className="w-full px-4 py-2 rounded-lg bg-white/5 border border-gray-600 focus:border-blue-400 focus:ring-1 focus:ring-blue-400 text-white"
                  placeholder="Enter your email address"
                  required
                />
              </div>

              <button
                type="submit"
                className="w-full bg-blue-500 hover:bg-blue-600 text-white font-semibold py-3 px-6 rounded-lg flex items-center justify-center gap-2 transition-colors"
              >
                <Send className="w-5 h-5" />
                Place Order
              </button>
            </form>
          </div>

          <div className="mt-8 text-center text-sm text-gray-400">
            <p>Need help? Contact our support team at support@example.com</p>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;