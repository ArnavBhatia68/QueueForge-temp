import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { Layers, Github } from 'lucide-react';
import { Metadata } from 'next';

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
          <Link href="https://github.com/ArnavBhatia68/QueueForge-temp" target="_blank">
            <Button variant="ghost" size="icon">
              <Github className="h-5 w-5" />
            </Button>
          </Link>

          <Link href="/login">
            <Button variant="ghost">Sign In</Button>
          </Link>

          <Link href="/register">
            <Button>Get Started</Button>
          </Link>
        </div>
      </header>

      <main className="flex-1 flex flex-col items-center justify-center px-6 text-center">
        <h1 className="text-5xl font-bold tracking-tight mb-4">
          QueueForge
        </h1>
        <p className="text-lg text-muted-foreground max-w-2xl mb-8">
          A modern, high-performance background job processing platform.
        </p>

        <div className="flex gap-4">
          <Link href="/register">
            <Button size="lg">Get Started</Button>
          </Link>
          <Link href="/login">
            <Button variant="outline" size="lg">Sign In</Button>
          </Link>
        </div>
      </main>
    </div>
  );
}
