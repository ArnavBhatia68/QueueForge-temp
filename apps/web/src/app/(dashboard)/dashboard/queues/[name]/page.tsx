'use client';

import Link from 'next/link';
import { useParams } from 'next/navigation';
import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { QueueStats, Job } from '@/types';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';

export default function QueueDetailPage() {
  const params = useParams();
  const name = params.name as string;

  const { data: queue } = useQuery({
    queryKey: ['queue', name],
    queryFn: async () => (await api.get<QueueStats>(`/queues/${name}`)).data,
  });

  const { data: jobs } = useQuery({
    queryKey: ['queue-jobs', name],
    queryFn: async () => (await api.get<Job[]>(`/queues/${name}/jobs`)).data,
    refetchInterval: 5000,
  });

  if (!queue) return <div>Loading queue...</div>;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Queue: {queue.name}</h2>
          <p className="text-muted-foreground">{queue.description || 'No description provided.'}</p>
        </div>
        <Link href={`/dashboard/jobs/new?queue=${queue.name}`} className="underline text-primary">Submit job to queue</Link>
      </div>

      <div className="grid gap-4 md:grid-cols-4">
        <Card><CardHeader><CardTitle>Total</CardTitle></CardHeader><CardContent>{queue.total_jobs}</CardContent></Card>
        <Card><CardHeader><CardTitle>Queued</CardTitle></CardHeader><CardContent>{queue.queued_jobs}</CardContent></Card>
        <Card><CardHeader><CardTitle>Running</CardTitle></CardHeader><CardContent>{queue.running_jobs}</CardContent></Card>
        <Card><CardHeader><CardTitle>Failed</CardTitle></CardHeader><CardContent>{queue.failed_jobs}</CardContent></Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Recent jobs</CardTitle>
          <CardDescription>Latest jobs in this queue.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          {jobs?.length ? jobs.map((job) => (
            <Link key={job.id} href={`/dashboard/jobs/${job.id}`} className="flex items-center justify-between rounded border p-3 hover:bg-muted/30">
              <div>
                <p className="font-medium">{job.name}</p>
                <p className="text-sm text-muted-foreground">{job.type}</p>
              </div>
              <Badge variant="outline" className="capitalize">{job.status}</Badge>
            </Link>
          )) : <p className="text-muted-foreground">No jobs in this queue yet.</p>}
        </CardContent>
      </Card>
    </div>
  );
}
