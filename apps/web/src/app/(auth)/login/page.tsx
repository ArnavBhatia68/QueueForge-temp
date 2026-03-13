'use client';

import Link from 'next/link';
import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/hooks/use-auth';
import { api } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Layers } from 'lucide-react';
import { toast } from 'sonner';

export default function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const router = useRouter();
  const { setAuth, setUser } = useAuthStore();

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);

    try {
      // 1. Get token
      const formData = new URLSearchParams();
      formData.append('username', email);
      formData.append('password', password);

      const tokenRes = await api.post('/auth/login', formData, {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
      });
      
      const token = tokenRes.data.access_token;
      setAuth(true, token);

      // 2. Get user profile
      const userRes = await api.get('/auth/me');
      setUser(userRes.data);

      toast.success('Logged in successfully');
      router.push('/dashboard');
    } catch {
      toast.error('Invalid email or password');
      setAuth(false);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-background p-4 flex-col">
      <div className="mb-8 flex items-center text-primary">
        <Layers className="h-8 w-8 mr-2" />
        <span className="text-2xl font-bold tracking-tight">QueueForge</span>
      </div>

      <Card className="w-full max-w-md">
        <CardHeader className="space-y-1">
          <CardTitle className="text-2xl font-bold tracking-tight">Sign in</CardTitle>
          <CardDescription>
            Enter your email below to login to your dashboard
          </CardDescription>
        </CardHeader>
        <form onSubmit={handleLogin}>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <Input 
                id="email" 
                type="email" 
                placeholder="m@example.com" 
                required 
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <Label htmlFor="password">Password</Label>
              </div>
              <Input 
                id="password" 
                type="password" 
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
            </div>
          </CardContent>
          <CardFooter className="flex flex-col gap-3">
            <Button className="w-full" type="submit" disabled={isLoading}>
              {isLoading ? "Signing in..." : "Sign In"}
            </Button>
            <p className="text-sm text-muted-foreground">
              New here?{' '}
              <Link href="/register" className="underline underline-offset-4">
                Create account
              </Link>
            </p>
          </CardFooter>
        </form>
      </Card>
      

    </div>
  );
}
