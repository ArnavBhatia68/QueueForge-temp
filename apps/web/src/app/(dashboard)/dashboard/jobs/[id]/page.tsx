'use client';

import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { JobDetail } from '@/types';
import { useParams } from 'next/navigation';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { formatDistanceToNow, format } from 'date-fns';
import { formatDuration } from '@/lib/utils';
import { Clock, PlayCircle, AlertCircle, CheckCircle2 } from 'lucide-react';


const formatJsonContent = (value: string | null | undefined, fallback: string) => {
  if (!value) return fallback;
  try {
    return JSON.stringify(JSON.parse(value), null, 2);
  } catch {
    return value;
  }
};

export default function JobDetailsPage() {
  const params = useParams();
  const id = params.id as string;

  const { data: job, isLoading } = useQuery({
    queryKey: ['job', id],
    queryFn: async () => {
      const { data } = await api.get<JobDetail>(`/jobs/${id}`);
      return data;
    },
    refetchInterval: (query) => {
        // Stop polling if done
        const jobStatus = query.state?.data?.status;
        if (jobStatus === 'succeeded' || jobStatus === 'failed' || jobStatus === 'cancelled') {
            return false;
        }
        return 3000;
    }
  });

  if (isLoading) return <div className="p-8">Loading job details...</div>;
  if (!job) return <div className="p-8">Job not found.</div>;

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'queued': return <Clock className="h-5 w-5 text-amber-500" />;
      case 'running': return <PlayCircle className="h-5 w-5 text-blue-500 animate-pulse" />;
      case 'succeeded': return <CheckCircle2 className="h-5 w-5 text-emerald-500" />;
      case 'failed': return <AlertCircle className="h-5 w-5 text-red-500" />;
      default: return <Clock className="h-5 w-5 text-gray-500" />;
    }
  };

  const duration = job.started_at && job.completed_at 
    ? formatDuration(new Date(job.completed_at).getTime() - new Date(job.started_at).getTime()) 
    : '-';

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold tracking-tight mb-2">Job #{job.id}</h2>
          <div className="flex items-center space-x-3 text-sm text-muted-foreground">
             <Badge variant="outline">{job.queue_name}</Badge>
             <span>Type: {job.type}</span>
             <span>Created: {formatDistanceToNow(new Date(job.created_at), { addSuffix: true })}</span>
          </div>
        </div>
        <div className="flex items-center space-x-2">
           {getStatusIcon(job.status)}
           <span className="font-medium capitalize text-lg">{job.status}</span>
        </div>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Execution Details</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4 text-sm">
            <div className="flex justify-between border-b pb-2">
              <span className="text-muted-foreground">Worker ID</span>
              <span className="font-mono">{job.worker_id || 'unassigned'}</span>
            </div>
            <div className="flex justify-between border-b pb-2">
              <span className="text-muted-foreground">Attempts</span>
              <span>{job.attempts} / {job.max_retries}</span>
            </div>
            <div className="flex justify-between border-b pb-2">
              <span className="text-muted-foreground">Duration</span>
              <span>{duration}</span>
            </div>
            {job.error_message && (
                <div className="mt-4 p-3 bg-red-500/10 text-red-500 rounded-md">
                    <span className="font-semibold block mb-1">Error:</span>
                    {job.error_message}
                </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Payload & Result</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
                <span className="text-sm text-muted-foreground font-medium mb-1 block">Input Payload</span>
                <pre className="bg-muted p-3 rounded-md text-xs overflow-auto max-h-32">
                    {formatJsonContent(job.payload, '{}')}
                </pre>
            </div>
            <div>
                <span className="text-sm text-muted-foreground font-medium mb-1 block">Output Result</span>
                <pre className="bg-muted p-3 rounded-md text-xs overflow-auto max-h-32">
                    {formatJsonContent(job.result, 'No result yet')}
                </pre>
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Execution Timeline</CardTitle>
          <CardDescription>Line by line execution logs from the worker.</CardDescription>
        </CardHeader>
        <CardContent>
            <div className="space-y-4">
                {job.logs.map((log) => (
                    <div key={log.id} className="flex space-x-4 text-sm">
                        <div className="w-48 text-muted-foreground whitespace-nowrap">
                            {format(new Date(log.timestamp), 'yyyy-MM-dd HH:mm:ss.SSS')}
                        </div>
                        <Badge variant="outline" className={
                            log.level === 'ERROR' ? 'text-red-500 border-red-500/50' : 
                            log.level === 'WARNING' ? 'text-amber-500 border-amber-500/50' : 
                            'text-muted-foreground'
                        }>
                            {log.level}
                        </Badge>
                        <div className="flex-1 font-mono text-xs mt-0.5">
                            {log.message}
                        </div>
                    </div>
                ))}
                {job.logs.length === 0 && (
                    <div className="text-muted-foreground text-center py-4">No logs available.</div>
                )}
            </div>
        </CardContent>
      </Card>
    </div>
  );
}
