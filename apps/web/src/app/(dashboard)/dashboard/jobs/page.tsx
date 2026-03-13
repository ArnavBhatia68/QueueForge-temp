import Link from 'next/link';
import { Metadata } from 'next';
import { JobsTable } from '@/components/dashboard/jobs-table';
import { Button } from '@/components/ui/button';

export const metadata: Metadata = {
  title: 'Jobs | QueueForge',
  description: 'Manage and monitor background jobs',
};

export default function JobsPage() {
  return (
    <div className="space-y-6 flex flex-col h-full">
      <div className="flex items-start justify-between">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Jobs</h2>
          <p className="text-muted-foreground">Monitor execution status, inspect logs, outputs, and retry failures.</p>
        </div>
        <Link href="/dashboard/jobs/new"><Button>Submit Job</Button></Link>
      </div>
      
      <JobsTable />
    </div>
  );
}
