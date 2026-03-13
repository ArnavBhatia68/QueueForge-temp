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

const TEXT_MODES = ['pretty_json', 'dedupe_lines', 'normalize_whitespace', 'extract_emails', 'counts'] as const;
const CSV_OPERATIONS = ['csv_to_json', 'dedupe_rows', 'validate_required_columns', 'summary_stats'] as const;

export default function NewJobPage() {
  const router = useRouter();
  const params = useSearchParams();
  const preferredQueue = params.get('queue') || '';

  const [queueName, setQueueName] = useState(preferredQueue);
  const [jobType, setJobType] = useState('webhook_request');
  const [jobName, setJobName] = useState('');
  const [priority, setPriority] = useState(0);
  const [maxRetries, setMaxRetries] = useState(3);

  const [webhookUrl, setWebhookUrl] = useState('');
  const [webhookMethod, setWebhookMethod] = useState('POST');
  const [webhookHeaders, setWebhookHeaders] = useState('{"Content-Type":"application/json"}');
  const [webhookBody, setWebhookBody] = useState('{"event":"queueforge.test"}');

  const [textMode, setTextMode] = useState<(typeof TEXT_MODES)[number]>('pretty_json');
  const [textInput, setTextInput] = useState('{"name":"Arnav","role":"student"}');

  const [csvOperation, setCsvOperation] = useState<(typeof CSV_OPERATIONS)[number]>('summary_stats');
  const [csvText, setCsvText] = useState('name,amount\nA,10\nB,20');
  const [requiredColumns, setRequiredColumns] = useState('name,amount');

  const { data: queues } = useQuery({
    queryKey: ['queues'],
    queryFn: async () => (await api.get<Queue[]>('/queues/')).data,
  });

  const payloadPreview = useMemo(() => {
    if (jobType === 'webhook_request') {
      let headers = {};
      let body: unknown = {};
      try { headers = JSON.parse(webhookHeaders); } catch {}
      try { body = JSON.parse(webhookBody); } catch {}
      return { url: webhookUrl, method: webhookMethod, headers, body };
    }
    if (jobType === 'text_transform') {
      return { mode: textMode, input: textInput };
    }
    return {
      operation: csvOperation,
      csv_text: csvText,
      ...(csvOperation === 'validate_required_columns'
        ? { required_columns: requiredColumns.split(',').map((v) => v.trim()).filter(Boolean) }
        : {}),
    };
  }, [jobType, webhookUrl, webhookMethod, webhookHeaders, webhookBody, textMode, textInput, csvOperation, csvText, requiredColumns]);

  const createMutation = useMutation({
    mutationFn: async () => {
      if (jobType === 'webhook_request' && !webhookUrl.trim()) {
        throw new Error('Webhook URL is required');
      }

      if (jobType === 'webhook_request') {
        JSON.parse(webhookHeaders);
        JSON.parse(webhookBody);
      }

      return api.post('/jobs/', {
        name: jobName,
        queue_name: queueName,
        type: jobType,
        priority,
        max_retries: maxRetries,
        payload: JSON.stringify(payloadPreview),
      });
    },
    onSuccess: ({ data }) => {
      toast.success('Job submitted');
      router.push(`/dashboard/jobs/${data.id}`);
    },
    onError: (error: unknown) => {
      const message = error && typeof error === 'object' && 'response' in error
        ? (error as { response?: { data?: { detail?: string } } }).response?.data?.detail
        : (error instanceof Error ? error.message : undefined);
      toast.error(message || 'Failed to submit job');
    },
  });

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">Submit Job</h2>
        <p className="text-muted-foreground">Use supported, production-ready job contracts only.</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Job configuration</CardTitle>
          <CardDescription>Queue + job type + required fields. Payload preview below is the exact API payload.</CardDescription>
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
                <option value="webhook_request">webhook_request</option>
                <option value="csv_processing">csv_processing</option>
                <option value="text_transform">text_transform</option>
              </select>
            </div>
          </div>

          <div className="grid md:grid-cols-3 gap-4">
            <div className="space-y-2 md:col-span-2">
              <Label>Job name</Label>
              <Input value={jobName} onChange={(e) => setJobName(e.target.value)} placeholder="Process customer data" />
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

          {jobType === 'webhook_request' && (
            <div className="space-y-3 rounded-md border p-3">
              <p className="text-sm font-medium">Webhook contract: url, method, optional headers/body</p>
              <div className="grid md:grid-cols-2 gap-3">
                <div className="space-y-2"><Label>URL</Label><Input value={webhookUrl} onChange={(e) => setWebhookUrl(e.target.value)} placeholder="https://httpbin.org/post" /></div>
                <div className="space-y-2"><Label>Method</Label><select className="w-full border rounded-md h-10 px-3" value={webhookMethod} onChange={(e) => setWebhookMethod(e.target.value)}><option>GET</option><option>POST</option><option>PUT</option><option>PATCH</option><option>DELETE</option></select></div>
              </div>
              <div className="space-y-2"><Label>Headers JSON</Label><textarea className="w-full border rounded-md p-2 font-mono text-xs min-h-20" value={webhookHeaders} onChange={(e) => setWebhookHeaders(e.target.value)} /></div>
              <div className="space-y-2"><Label>Body JSON</Label><textarea className="w-full border rounded-md p-2 font-mono text-xs min-h-24" value={webhookBody} onChange={(e) => setWebhookBody(e.target.value)} /></div>
            </div>
          )}

          {jobType === 'text_transform' && (
            <div className="space-y-3 rounded-md border p-3">
              <p className="text-sm font-medium">Text transform contract: mode + input</p>
              <div className="space-y-2">
                <Label>Mode</Label>
                <select className="w-full border rounded-md h-10 px-3" value={textMode} onChange={(e) => setTextMode(e.target.value as (typeof TEXT_MODES)[number])}>
                  {TEXT_MODES.map((mode) => <option key={mode} value={mode}>{mode}</option>)}
                </select>
              </div>
              <div className="space-y-2"><Label>Input</Label><textarea className="w-full border rounded-md p-2 font-mono text-xs min-h-28" value={textInput} onChange={(e) => setTextInput(e.target.value)} /></div>
            </div>
          )}

          {jobType === 'csv_processing' && (
            <div className="space-y-3 rounded-md border p-3">
              <p className="text-sm font-medium">CSV contract: operation + csv_text (+required_columns for validate_required_columns)</p>
              <div className="space-y-2">
                <Label>Operation</Label>
                <select className="w-full border rounded-md h-10 px-3" value={csvOperation} onChange={(e) => setCsvOperation(e.target.value as (typeof CSV_OPERATIONS)[number])}>
                  {CSV_OPERATIONS.map((op) => <option key={op} value={op}>{op}</option>)}
                </select>
              </div>
              <div className="space-y-2"><Label>CSV Text</Label><textarea className="w-full border rounded-md p-2 font-mono text-xs min-h-28" value={csvText} onChange={(e) => setCsvText(e.target.value)} /></div>
              {csvOperation === 'validate_required_columns' && (
                <div className="space-y-2"><Label>Required columns (comma-separated)</Label><Input value={requiredColumns} onChange={(e) => setRequiredColumns(e.target.value)} /></div>
              )}
            </div>
          )}

          <div className="space-y-2">
            <Label>Payload preview (JSON sent to API)</Label>
            <pre className="w-full border rounded-md p-3 text-xs font-mono overflow-auto bg-muted">{JSON.stringify(payloadPreview, null, 2)}</pre>
          </div>

          <Button disabled={!queueName || !jobName.trim() || createMutation.isPending} onClick={() => createMutation.mutate()}>
            {createMutation.isPending ? 'Submitting…' : 'Submit job'}
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
