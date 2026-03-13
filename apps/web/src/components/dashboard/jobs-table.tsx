'use client';

import Link from 'next/link';
import { useMemo, useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { Job, JobStatus } from '@/types';
import { formatDuration } from '@/lib/utils';
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
  const [searchTerm, setSearchTerm] = useState('');
  const queryClient = useQueryClient();

  const { data: jobs, isLoading } = useQuery({
    queryKey: ['jobs', statusFilter],
    queryFn: async () => {
      const { data } = await api.get<Job[]>('/jobs/', {
        params: { limit: 100, ...(statusFilter && { status: statusFilter }) },
      });
      return data;
    },
    refetchInterval: 3000,
  });

  const filteredJobs = useMemo(() => {
    if (!jobs) return [];
    const term = searchTerm.trim().toLowerCase();
    if (!term) return jobs;

    return jobs.filter((job) => {
      const searchable = `${job.id} ${job.type} ${job.queue_name} ${job.status} ${job.payload ?? ''}`.toLowerCase();
      return searchable.includes(term);
    });
  }, [jobs, searchTerm]);

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

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'queued': return 'bg-amber-500/10 text-amber-500 hover:bg-amber-500/20';
      case 'running': return 'bg-blue-500/10 text-blue-500 hover:bg-blue-500/20';
      case 'succeeded': return 'bg-emerald-500/10 text-emerald-500 hover:bg-emerald-500/20';
      case 'failed': return 'bg-red-500/10 text-red-500 hover:bg-red-500/20';
      case 'cancelled': return 'bg-slate-500/10 text-slate-500 hover:bg-slate-500/20';
      case 'retrying': return 'bg-purple-500/10 text-purple-500 hover:bg-purple-500/20';
      default: return 'bg-gray-500/10 text-gray-500';
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between gap-2">
        <div className="flex w-full max-w-sm items-center space-x-2 border rounded-md px-3 py-1 bg-background focus-within:ring-1 focus-within:ring-primary">
          <Search className="h-4 w-4 text-muted-foreground mr-2" />
          <input
            className="flex h-8 w-full bg-transparent p-0 placeholder:text-muted-foreground focus-visible:outline-none disabled:cursor-not-allowed disabled:opacity-50 text-sm border-0"
            placeholder="Search job ID, type, queue, status, or payload"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>
        <div className="flex gap-2">
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value as JobStatus | '')}
            className="h-10 rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
          >
            <option value="">All Statuses</option>
            <option value="queued">Queued</option>
            <option value="running">Running</option>
            <option value="succeeded">Succeeded</option>
            <option value="failed">Failed</option>
            <option value="cancelled">Cancelled</option>
          </select>
        </div>
      </div>

      <div className="rounded-md border bg-card">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="w-[100px]">Job ID</TableHead>
              <TableHead>Queue</TableHead>
              <TableHead>Type</TableHead>
              <TableHead>Status</TableHead>
              <TableHead className="text-right">Timing</TableHead>
              <TableHead className="text-right">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {isLoading ? (
              <TableRow>
                <TableCell colSpan={6} className="h-24 text-center">
                  Loading jobs...
                </TableCell>
              </TableRow>
            ) : filteredJobs.length === 0 ? (
              <TableRow>
                <TableCell colSpan={6} className="h-24 text-center text-muted-foreground bg-muted/50">
                  No jobs found.
                </TableCell>
              </TableRow>
            ) : (
              filteredJobs.map((job) => (
                <TableRow key={job.id}>
                  <TableCell className="font-medium text-xs">#{job.id}</TableCell>
                  <TableCell>
                    <Badge variant="outline" className="font-mono">{job.queue_name}</Badge>
                  </TableCell>
                  <TableCell className="text-sm">{job.type}</TableCell>
                  <TableCell>
                    <Badge variant="secondary" className={getStatusColor(job.status)}>
                      {job.status}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-right text-xs text-muted-foreground space-y-1">
                    <div>{formatDistanceToNow(new Date(job.created_at), { addSuffix: true })}</div>
                    {job.started_at && job.completed_at && (
                      <div>{formatDuration(new Date(job.completed_at).getTime() - new Date(job.started_at).getTime())}</div>
                    )}
                  </TableCell>
                  <TableCell className="text-right space-x-2">
                    {(job.status === 'failed' || job.status === 'cancelled') && (
                      <Button variant="ghost" size="icon" onClick={() => retryMutation.mutate(job.id)} title="Retry">
                        <RefreshCcw className="h-4 w-4 text-emerald-500" />
                      </Button>
                    )}
                    {job.status === 'queued' && (
                      <Button variant="ghost" size="icon" onClick={() => cancelMutation.mutate(job.id)} title="Cancel">
                        <XCircle className="h-4 w-4 text-slate-500" />
                      </Button>
                    )}
                    <Link href={`/dashboard/jobs/${job.id}`}>
                      <Button variant="ghost" size="icon" title="Details">
                        <Info className="h-4 w-4" />
                      </Button>
                    </Link>
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
