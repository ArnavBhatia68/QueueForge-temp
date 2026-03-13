'use client';

import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { AnalyticsOverview } from '@/types';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

export function OverviewCards() {
  const { data } = useQuery({
    queryKey: ['analytics', 'overview'],
    queryFn: async () => (await api.get<AnalyticsOverview>('/analytics/overview')).data,
    refetchInterval: 5000,
  });

  if (!data) return null;

  const cards = [
    ['Total Queues', data.total_queues],
    ['Total Jobs', data.total_jobs],
    ['Queued', data.queued_jobs],
    ['Running', data.running_jobs],
    ['Succeeded', data.succeeded_jobs],
    ['Failed', data.failed_jobs],
  ];

  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
      {cards.map(([label, value]) => (
        <Card key={label}>
          <CardHeader className="pb-2"><CardTitle className="text-sm font-medium">{label}</CardTitle></CardHeader>
          <CardContent><div className="text-2xl font-bold">{value}</div></CardContent>
        </Card>
      ))}
    </div>
  );
}
