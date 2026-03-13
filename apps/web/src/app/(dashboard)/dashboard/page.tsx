'use client';

import Link from 'next/link';
import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { OverviewCards } from '@/components/dashboard/overview-cards';
import { RecentActivity } from '@/components/dashboard/RecentActivity';
import { JobStatusChart } from '@/components/charts/JobStatusChart';
import { Queue } from '@/types';
import { Button } from '@/components/ui/button';

export default function DashboardPage() {
  const { data: queues } = useQuery({ queryKey: ['queues'], queryFn: async () => (await api.get<Queue[]>('/queues/')).data });
  const { data: recent } = useQuery({ queryKey: ['analytics', 'recent'], queryFn: async () => (await api.get('/analytics/recent')).data });

  const isEmpty = !queues?.length && !recent?.length;

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">Operations Dashboard</h2>
        <p className="text-muted-foreground">QueueForge runs your background work and keeps execution status, logs, and outputs in one place.</p>
      </div>

      {isEmpty ? (
        <div className="rounded-lg border border-dashed p-8 space-y-4">
          <p className="font-semibold">Get started by creating a queue and submitting your first job.</p>
          <p className="text-sm text-muted-foreground">Supported job types: Webhook / HTTP request, CSV processing, and text/data transformation.</p>
          <div className="flex gap-3">
            <Link href="/dashboard/queues"><Button>Create Queue</Button></Link>
            <Link href="/dashboard/jobs/new"><Button variant="outline">Submit Job</Button></Link>
          </div>
        </div>
      ) : (
        <>
          <OverviewCards />
          <div className="grid gap-4 md:grid-cols-7">
            <JobStatusChart />
            <RecentActivity />
          </div>
        </>
      )}
    </div>
  );
}
