'use client';

import { useMemo, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { useMutation, useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { Queue } from '@/types';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { toast } from 'sonner';

export default function NewJobPage() {
  const router = useRouter();
  const params = useSearchParams();
  const preferredQueue = params.get('queue') || '';

  const [queueName, setQueueName] = useState(preferredQueue);
  const [jobType, setJobType] = useState('webhook_request');
  const [jobName, setJobName] = useState('');
  const [priority, setPriority] = useState(0);
  const [maxRetries, setMaxRetries] = useState(3);
  const [payloadText, setPayloadText] = useState('');

  const { data: queues } = useQuery({
    queryKey: ['queues'],
    queryFn: async () => (await api.get<Queue[]>('/queues/')).data,
  });

  const payloadTemplate = useMemo(() => {
    if (jobType === 'webhook_request') return '{\n  "url": "https://httpbin.org/post",\n  "method": "POST",\n  "headers": {"X-Trace": "queueforge"},\n  "body": {"event": "invoice.created"}\n}';
    if (jobType === 'csv_processing') return '{\n  "operation": "summary_statistics",\n  "csv_text": "name,email\\nAda,ada@example.com\\nLin,lin@example.com"\n}';
    return '{\n  "mode": "extract_emails",\n  "input": "Contact us: a@example.com and b@example.com"\n}';
  }, [jobType]);

  const createMutation = useMutation({
    mutationFn: async () => {
      let payloadObj: unknown;
      try {
        payloadObj = JSON.parse(payloadText || payloadTemplate);
      } catch {
        throw new Error('Payload must be valid JSON.');
      }
      return api.post('/jobs/', {
        name: jobName,
        queue_name: queueName,
        type: jobType,
        priority,
        max_retries: maxRetries,
        payload: JSON.stringify(payloadObj),
      });
    },
    onSuccess: ({ data }) => {
      toast.success('Job submitted');
      router.push(`/dashboard/jobs/${data.id}`);
    },
    onError: (error: unknown) => {
      const message = error && typeof error === 'object' && 'response' in error
        ? (error as { response?: { data?: { detail?: string } } }).response?.data?.detail
        : undefined;
      toast.error(message || 'Failed to submit job');
    },
  });

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">Submit Job</h2>
        <p className="text-muted-foreground">Send real background tasks to a queue using your own input.</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Job configuration</CardTitle>
          <CardDescription>Choose queue, type, and payload. Jobs are processed asynchronously by workers.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label>Queue</Label>
              <select className="w-full border rounded-md h-10 px-3" value={queueName} onChange={(e) => setQueueName(e.target.value)}>
                <option value="">Select queue</option>
                {queues?.map((q) => <option key={q.id} value={q.name}>{q.name}</option>)}
              </select>
            </div>
            <div className="space-y-2">
              <Label>Job type</Label>
              <select className="w-full border rounded-md h-10 px-3" value={jobType} onChange={(e) => setJobType(e.target.value)}>
                <option value="webhook_request">Webhook / HTTP Request</option>
                <option value="csv_processing">CSV Processing</option>
                <option value="text_transform">Text / Data Transformation</option>
              </select>
            </div>
          </div>

          <div className="grid md:grid-cols-3 gap-4">
            <div className="space-y-2 md:col-span-2">
              <Label>Job name</Label>
              <Input value={jobName} onChange={(e) => setJobName(e.target.value)} placeholder="Notify billing endpoint" />
            </div>
            <div className="space-y-2">
              <Label>Priority</Label>
              <Input type="number" value={priority} onChange={(e) => setPriority(Number(e.target.value))} />
            </div>
          </div>

          <div className="space-y-2">
            <Label>Max retries</Label>
            <Input type="number" min={0} max={10} value={maxRetries} onChange={(e) => setMaxRetries(Number(e.target.value))} />
          </div>

          <div className="space-y-2">
            <Label>Payload (JSON)</Label>
            <textarea className="w-full border rounded-md p-3 text-sm font-mono min-h-[220px]" value={payloadText || payloadTemplate} onChange={(e) => setPayloadText(e.target.value)} />
          </div>

          <Button disabled={!queueName || !jobName.trim() || createMutation.isPending} onClick={() => createMutation.mutate()}>
            {createMutation.isPending ? 'Submitting…' : 'Submit job'}
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
