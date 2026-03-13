'use client';

import { useQuery } from '@tanstack/react-query';
import Link from 'next/link';
import { formatDistanceToNow } from 'date-fns';
import { api } from '@/lib/api';
import { parseApiDate } from '@/lib/utils';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { JobStatus } from '@/types';

interface RecentJobItem {
  id: number;
  name: string;
  type: string;
  queue_name: string;
  status: JobStatus;
  created_at: string;
}

const STATUS_STYLES: Record<JobStatus, string> = {
  succeeded: 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30',
  failed: 'bg-red-500/15 text-red-400 border-red-500/30',
  running: 'bg-blue-500/15 text-blue-400 border-blue-500/30',
  queued: 'bg-slate-500/15 text-slate-400 border-slate-500/30',
  retrying: 'bg-amber-500/15 text-amber-400 border-amber-500/30',
  cancelled: 'bg-zinc-500/15 text-zinc-400 border-zinc-500/30',
};

const STATUS_DOT: Record<JobStatus, string> = {
  succeeded: 'bg-emerald-400',
  failed: 'bg-red-400',
  running: 'bg-blue-400 animate-pulse',
  queued: 'bg-slate-400',
  retrying: 'bg-amber-400',
  cancelled: 'bg-zinc-400',
};

export function RecentActivity() {
  const { data, isLoading } = useQuery<RecentJobItem[]>({
    queryKey: ['analytics', 'recent'],
    queryFn: async () => {
      const { data } = await api.get<RecentJobItem[]>('/analytics/recent');
      return data;
    },
    refetchInterval: 5_000,
  });

  return (
    <Card className="col-span-3">
      <CardHeader>
        <CardTitle>Recent Activity</CardTitle>
        <CardDescription>Latest jobs across all queues</CardDescription>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <div className="space-y-3">
            {[...Array(6)].map((_, i) => (
              <div key={i} className="flex items-center gap-3 animate-pulse">
                <div className="h-2 w-2 rounded-full bg-muted flex-shrink-0" />
                <div className="flex-1 space-y-1">
                  <div className="h-3 w-3/4 bg-muted rounded" />
                  <div className="h-2 w-1/2 bg-muted rounded" />
                </div>
                <div className="h-5 w-16 bg-muted rounded-full" />
              </div>
            ))}
          </div>
        ) : !data?.length ? (
          <div className="flex flex-col items-center justify-center h-48 text-muted-foreground gap-2">
            <p className="text-sm">No jobs yet.</p>
          </div>
        ) : (
          <div className="space-y-1">
            {data.map((job) => (
              <Link
                key={job.id}
                href={`/dashboard/jobs/${job.id}`}
                className="flex items-center gap-3 px-2 py-2.5 rounded-lg hover:bg-muted/50 transition-colors group"
              >
                <span
                  className={`h-2 w-2 rounded-full flex-shrink-0 ${STATUS_DOT[job.status]}`}
                />
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium leading-none truncate group-hover:text-foreground text-foreground/80">
                    {job.name}
                    <span className="ml-2 text-xs text-muted-foreground font-normal">
                      #{job.id}
                    </span>
                  </p>
                  <p className="text-xs text-muted-foreground mt-0.5">
                    {job.queue_name} ·{' '}
                    {formatDistanceToNow(parseApiDate(job.created_at), { addSuffix: true })}
                  </p>
                </div>
                <Badge
                  variant="outline"
                  className={`text-[10px] px-2 py-0.5 capitalize font-medium ${STATUS_STYLES[job.status]}`}
                >
                  {job.status}
                </Badge>
              </Link>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
