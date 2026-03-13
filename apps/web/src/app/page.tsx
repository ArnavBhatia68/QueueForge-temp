import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { Layers, Activity, Shield, Zap, ArrowRight, Github } from 'lucide-react';
import { Metadata } from 'next';
import { Badge } from '@/components/ui/badge';

export const metadata: Metadata = {
  title: 'QueueForge | Production Job Queues',
  description: 'A modern, high-performance background job processing platform.',
};

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-background text-foreground flex flex-col">
      <header className="px-6 h-16 flex items-center justify-between border-b bg-background/80 backdrop-blur-md sticky top-0 z-50">
        <div className="flex items-center">
          <Layers className="h-6 w-6 text-primary mr-2" />
          <span className="font-bold text-lg tracking-tight">QueueForge</span>
        </div>
        <div className="flex items-center gap-4">
          <Link href="https://github.com/arnavbhatia/QueueForge" target="_blank">
            <Button variant="ghost" size="icon">
              <Github className="h-5 w-5" />
            </Button>
          </Link>
          <Link href="/login">
            <Button variant="ghost">Sign In</Button>
          </Link>
          <Link href="/register">
          <Link href="/login">
            <Button>Get Started</Button>
          </Link>
        </div>
      </header>

      <main className="flex-1 text-center py-20 px-6 sm:px-12 flex flex-col items-center justify-center max-w-5xl mx-auto">
        <Badge variant="outline" className="mb-6 px-3 py-1 bg-primary/10 text-primary border-primary/20">
          Open Source Release 1.0 <Zap className="h-3 w-3 ml-1 inline" />
        </Badge>
        
        <h1 className="text-4xl sm:text-6xl font-extrabold tracking-tight mb-8">
          Distributed job queues that <br className="hidden sm:block" />
          <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-500 to-emerald-400">
            scale with your application.
          </span>
        </h1>
        
        <p className="text-xl text-muted-foreground mb-10 max-w-2xl">
          QueueForge is a production-grade background job processing platform. 
          Monitor queues in real-time, retry failed tasks automatically, and integrate 
          with any stack in minutes.
        </p>
        
        <div className="flex flex-col sm:flex-row gap-4 mb-20">
          <Link href="/login">
            <Button size="lg" className="h-12 px-8 text-base">
              Explore Dashboard
              <ArrowRight className="ml-2 h-4 w-4" />
            </Button>
          </Link>
          <Link href="https://github.com/arnavbhatia/QueueForge" target="_blank">
            <Button size="lg" variant="outline" className="h-12 px-8 text-base">
              View on GitHub
            </Button>
          </Link>
        </div>

        {/* Feature Grid */}
        <div className="grid sm:grid-cols-3 gap-8 text-left w-full border-t pt-20">
          <div className="space-y-4">
            <div className="h-12 w-12 rounded-lg bg-blue-500/10 flex items-center justify-center">
              <Activity className="h-6 w-6 text-blue-500" />
            </div>
            <h3 className="text-xl font-bold">Real-time Analytics</h3>
            <p className="text-muted-foreground">
              Monitor queue throughput, success rates, and active workers instantly with our polished dashboard.
            </p>
          </div>
          <div className="space-y-4">
            <div className="h-12 w-12 rounded-lg bg-emerald-500/10 flex items-center justify-center">
              <Zap className="h-6 w-6 text-emerald-500" />
            </div>
            <h3 className="text-xl font-bold">High Performance</h3>
            <p className="text-muted-foreground">
              Backed by Redis and asynchronous Python workers to process thousands of jobs per second.
            </p>
          </div>
          <div className="space-y-4">
            <div className="h-12 w-12 rounded-lg bg-purple-500/10 flex items-center justify-center">
              <Shield className="h-6 w-6 text-purple-500" />
            </div>
            <h3 className="text-xl font-bold">Reliable Execution</h3>
            <p className="text-muted-foreground">
              Automatic retries on failure, exponential backoff, and state persistence in PostgreSQL.
            </p>
          </div>
        </div>
      </main>

      <footer className="border-t py-8 px-6 text-center text-muted-foreground text-sm">
        <p>&copy; {new Date().getFullYear()} QueueForge. Built for modern distributed workloads.</p>
      </footer>
    </div>
  );
}
