'use client';

import Link from 'next/link';
import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { Job, JobStatus, Queue } from '@/types';
import { formatDistanceToNow } from 'date-fns';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { RefreshCcw, XCircle, Search, Info } from 'lucide-react';
import { toast } from 'sonner';

export function JobsTable() {
  const [statusFilter, setStatusFilter] = useState<JobStatus | ''>('');
  const [queueFilter, setQueueFilter] = useState('');
  const [typeFilter, setTypeFilter] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  const queryClient = useQueryClient();

  const { data: queues } = useQuery({
    queryKey: ['queues'],
    queryFn: async () => (await api.get<Queue[]>('/queues/')).data,
  });

  const { data: jobs, isLoading } = useQuery({
    queryKey: ['jobs', statusFilter, queueFilter, typeFilter, searchTerm],
    queryFn: async () => {
      const { data } = await api.get<Job[]>('/jobs/', {
        params: {
          limit: 100,
          ...(statusFilter && { status: statusFilter }),
          ...(queueFilter && { queue_name: queueFilter }),
          ...(typeFilter && { job_type: typeFilter }),
          ...(searchTerm.trim() && { search: searchTerm.trim() }),
        },
      });
      return data;
    },
    refetchInterval: 3000,
  });

  const retryMutation = useMutation({
    mutationFn: (id: number) => api.post(`/jobs/${id}/retry/`),
    onSuccess: () => {
      toast.success('Job queued for retry');
      queryClient.invalidateQueries({ queryKey: ['jobs'] });
    },
    onError: () => toast.error('Failed to retry job'),
  });

  const cancelMutation = useMutation({
    mutationFn: (id: number) => api.post(`/jobs/${id}/cancel/`),
    onSuccess: () => {
      toast.success('Job cancelled');
      queryClient.invalidateQueries({ queryKey: ['jobs'] });
    },
    onError: () => toast.error('Failed to cancel job'),
  });

  return (
    <div className="space-y-4">
      <div className="grid md:grid-cols-4 gap-2">
        <div className="flex w-full items-center space-x-2 border rounded-md px-3 py-1 bg-background">
          <Search className="h-4 w-4 text-muted-foreground mr-2" />
          <input className="flex h-8 w-full bg-transparent p-0 focus-visible:outline-none text-sm border-0" placeholder="Search by ID, name, queue, type" value={searchTerm} onChange={(e) => setSearchTerm(e.target.value)} />
        </div>
        <select value={queueFilter} onChange={(e) => setQueueFilter(e.target.value)} className="h-10 rounded-md border px-3 text-sm">
          <option value="">All queues</option>
          {queues?.map((q) => <option key={q.id} value={q.name}>{q.name}</option>)}
        </select>
        <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value as JobStatus | '')} className="h-10 rounded-md border px-3 text-sm">
          <option value="">All statuses</option>
          <option value="queued">Queued</option><option value="running">Running</option><option value="succeeded">Succeeded</option><option value="failed">Failed</option><option value="cancelled">Cancelled</option>
        </select>
        <select value={typeFilter} onChange={(e) => setTypeFilter(e.target.value)} className="h-10 rounded-md border px-3 text-sm">
          <option value="">All job types</option>
          <option value="webhook_request">Webhook / HTTP</option>
          <option value="csv_processing">CSV Processing</option>
          <option value="text_transform">Text Transform</option>
        </select>
      </div>

      <div className="rounded-md border bg-card">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>ID</TableHead><TableHead>Name</TableHead><TableHead>Queue</TableHead><TableHead>Type</TableHead><TableHead>Status</TableHead><TableHead>Priority</TableHead><TableHead>Attempts</TableHead><TableHead>Created</TableHead><TableHead>Started</TableHead><TableHead>Completed</TableHead><TableHead>Worker</TableHead><TableHead>Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {isLoading ? <TableRow><TableCell colSpan={12}>Loading jobs...</TableCell></TableRow> : !jobs?.length ? <TableRow><TableCell colSpan={12} className="text-muted-foreground">No jobs yet. Submit a job to process a webhook, CSV, or text transformation.</TableCell></TableRow> : (
              jobs.map((job) => (
                <TableRow key={job.id}>
                  <TableCell>#{job.id}</TableCell>
                  <TableCell>{job.name}</TableCell>
                  <TableCell>{job.queue_name}</TableCell>
                  <TableCell>{job.type}</TableCell>
                  <TableCell><Badge variant="outline" className="capitalize">{job.status}</Badge></TableCell>
                  <TableCell>{job.priority}</TableCell>
                  <TableCell>{job.attempts}/{job.max_retries}</TableCell>
                  <TableCell>{formatDistanceToNow(new Date(job.created_at), { addSuffix: true })}</TableCell>
                  <TableCell>{job.started_at ? formatDistanceToNow(new Date(job.started_at), { addSuffix: true }) : '—'}</TableCell>
                  <TableCell>{job.completed_at ? formatDistanceToNow(new Date(job.completed_at), { addSuffix: true }) : '—'}</TableCell>
                  <TableCell>{job.worker_id || '—'}</TableCell>
                  <TableCell className="space-x-1">
                    {(job.status === 'failed' || job.status === 'cancelled') && <Button variant="ghost" size="icon" onClick={() => retryMutation.mutate(job.id)} title="Retry"><RefreshCcw className="h-4 w-4" /></Button>}
                    {(job.status === 'queued' || job.status === 'running') && <Button variant="ghost" size="icon" onClick={() => cancelMutation.mutate(job.id)} title="Cancel"><XCircle className="h-4 w-4" /></Button>}
                    <Link href={`/dashboard/jobs/${job.id}`}><Button variant="ghost" size="icon" title="Details"><Info className="h-4 w-4" /></Button></Link>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}
