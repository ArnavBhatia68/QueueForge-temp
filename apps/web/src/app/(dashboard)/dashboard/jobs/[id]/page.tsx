'use client';

import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { JobDetail } from '@/types';
import { useParams } from 'next/navigation';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { format } from 'date-fns';

const pretty = (value: string | null | undefined, fallback: string) => {
  if (!value) return fallback;
  try { return JSON.stringify(JSON.parse(value), null, 2); } catch { return value; }
};

export default function JobDetailsPage() {
  const params = useParams();
  const id = params.id as string;

  const { data: job } = useQuery({
    queryKey: ['job', id],
    queryFn: async () => (await api.get<JobDetail>(`/jobs/${id}`)).data,
    refetchInterval: (q) => {
      const status = q.state.data?.status;
      return status && ['succeeded', 'failed', 'cancelled'].includes(status) ? false : 3000;
    },
  });

  if (!job) return <div className="p-8">Loading job details...</div>;

  const durationMs = job.started_at && job.completed_at
    ? new Date(job.completed_at).getTime() - new Date(job.started_at).getTime()
    : null;

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">{job.name}</h2>
        <p className="text-muted-foreground">Job #{job.id}</p>
      </div>

      <Card>
        <CardHeader><CardTitle>Overview</CardTitle></CardHeader>
        <CardContent className="grid md:grid-cols-2 gap-3 text-sm">
          <p><strong>ID:</strong> {job.id}</p><p><strong>Queue:</strong> {job.queue_name}</p>
          <p><strong>Type:</strong> {job.type}</p><p><strong>Status:</strong> <Badge variant="outline" className="capitalize">{job.status}</Badge></p>
        </CardContent>
      </Card>

      <div className="grid md:grid-cols-2 gap-6">
        <Card>
          <CardHeader><CardTitle>Input</CardTitle></CardHeader>
          <CardContent><pre className="bg-muted rounded p-3 text-xs overflow-auto max-h-64">{pretty(job.payload, 'No input payload')}</pre></CardContent>
        </Card>
        <Card>
          <CardHeader><CardTitle>Output</CardTitle></CardHeader>
          <CardContent><pre className="bg-muted rounded p-3 text-xs overflow-auto max-h-64">{pretty(job.result, 'No output yet')}</pre></CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader><CardTitle>Execution</CardTitle></CardHeader>
        <CardContent className="grid md:grid-cols-2 gap-3 text-sm">
          <p><strong>Attempts:</strong> {job.attempts} / {job.max_retries}</p>
          <p><strong>Worker ID:</strong> {job.worker_id || 'Unassigned'}</p>
          <p><strong>Created:</strong> {format(new Date(job.created_at), 'yyyy-MM-dd HH:mm:ss')}</p>
          <p><strong>Started:</strong> {job.started_at ? format(new Date(job.started_at), 'yyyy-MM-dd HH:mm:ss') : '—'}</p>
          <p><strong>Completed:</strong> {job.completed_at ? format(new Date(job.completed_at), 'yyyy-MM-dd HH:mm:ss') : '—'}</p>
          <p><strong>Duration:</strong> {durationMs !== null ? `${durationMs}ms` : '—'}</p>
          {job.error_message && <p className="md:col-span-2 text-red-600"><strong>Error:</strong> {job.error_message}</p>}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Logs timeline</CardTitle>
          <CardDescription>Queued, processing, retries, and completion logs from the worker.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          {job.logs.length === 0 ? <p className="text-muted-foreground">No logs available yet.</p> : job.logs.map((log) => (
            <div key={log.id} className="text-sm border-l pl-3">
              <p className="text-xs text-muted-foreground">{format(new Date(log.timestamp), 'yyyy-MM-dd HH:mm:ss.SSS')} · {log.level}</p>
              <p className="font-mono text-xs">{log.message}</p>
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  );
}
