/*
  # Create orders table for USDT transactions

  1. New Tables
    - `orders`
      - `id` (uuid, primary key)
      - `created_at` (timestamp with timezone)
      - `wallet_address` (text, required)
      - `amount` (numeric, required)
      - `email` (text, required)
      - `status` (text, default: 'pending')
      
  2. Security
    - Enable RLS on `orders` table
    - Add policies for:
      - Inserting new orders (public access)
      - Reading own orders (based on email)
*/

CREATE TABLE IF NOT EXISTS orders (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at timestamptz DEFAULT now(),
    wallet_address text NOT NULL,
    amount numeric NOT NULL CHECK (amount > 0),
    email text NOT NULL,
    status text NOT NULL DEFAULT 'pending'
);

-- Enable Row Level Security
ALTER TABLE orders ENABLE ROW LEVEL SECURITY;

-- Allow anyone to insert new orders
CREATE POLICY "Allow public to insert orders"
    ON orders
    FOR INSERT
    TO public
    WITH CHECK (true);

-- Allow users to read their own orders
CREATE POLICY "Users can view own orders"
    ON orders
    FOR SELECT
    TO public
    USING (email = current_user);