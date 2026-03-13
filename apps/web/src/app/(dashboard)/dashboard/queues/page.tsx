'use client';

import Link from 'next/link';
import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { parseApiDate } from '@/lib/utils';
import { QueueStats } from '@/types';
import { formatDistanceToNow } from 'date-fns';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { toast } from 'sonner';

export default function QueuesPage() {
  const queryClient = useQueryClient();
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');

  const { data: queues, isLoading } = useQuery({
    queryKey: ['queues'],
    queryFn: async () => {
      const { data } = await api.get<QueueStats[]>('/queues/');
      return data;
    },
    refetchInterval: 5000,
  });

  const createQueueMutation = useMutation({
    mutationFn: async () => api.post('/queues/', { name, description: description || null }),
    onSuccess: () => {
      toast.success('Queue created');
      setName('');
      setDescription('');
      queryClient.invalidateQueries({ queryKey: ['queues'] });
    },
    onError: () => toast.error('Could not create queue'),
  });

  const hasQueues = (queues?.length ?? 0) > 0;

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">Queues</h2>
        <p className="text-muted-foreground">Create queues to organize background workloads by purpose.</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Create Queue</CardTitle>
          <CardDescription>Queue names must be unique and are used by workers for routing.</CardDescription>
        </CardHeader>
        <CardContent className="grid gap-4 md:grid-cols-3">
          <div className="space-y-2">
            <Label htmlFor="queueName">Queue name</Label>
            <Input id="queueName" value={name} onChange={(e) => setName(e.target.value)} placeholder="invoices" />
          </div>
          <div className="space-y-2 md:col-span-2">
            <Label htmlFor="queueDescription">Description</Label>
            <Input id="queueDescription" value={description} onChange={(e) => setDescription(e.target.value)} placeholder="Processes invoice webhooks and CSV imports" />
          </div>
          <div className="md:col-span-3">
            <Button disabled={!name.trim() || createQueueMutation.isPending} onClick={() => createQueueMutation.mutate()}>
              {createQueueMutation.isPending ? 'Creating…' : 'Create Queue'}
            </Button>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Your queues</CardTitle>
          <CardDescription>Operational queue status with workload breakdown.</CardDescription>
        </CardHeader>
        <CardContent>
          {!isLoading && !hasQueues ? (
            <div className="rounded-md border border-dashed p-8 text-center text-muted-foreground">
              <p className="font-medium text-foreground">Create a queue to organize background work.</p>
              <p className="mt-2 text-sm">Example queues: webhooks, csv-ops, customer-data.</p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Name</TableHead>
                  <TableHead>Description</TableHead>
                  <TableHead>Total jobs</TableHead>
                  <TableHead>Queued / Running / Failed</TableHead>
                  <TableHead>Last activity</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {isLoading ? (
                  <TableRow><TableCell colSpan={5}>Loading queues...</TableCell></TableRow>
                ) : (
                  queues?.map((queue) => (
                    <TableRow key={queue.id}>
                      <TableCell>
                        <Link className="font-semibold text-primary hover:underline" href={`/dashboard/queues/${queue.name}`}>
                          {queue.name}
                        </Link>
                      </TableCell>
                      <TableCell>{queue.description || '—'}</TableCell>
                      <TableCell>{queue.total_jobs}</TableCell>
                      <TableCell>{queue.queued_jobs} / {queue.running_jobs} / {queue.failed_jobs}</TableCell>
                      <TableCell>{queue.last_activity_at ? formatDistanceToNow(parseApiDate(queue.last_activity_at), { addSuffix: true }) : 'No activity yet'}</TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
