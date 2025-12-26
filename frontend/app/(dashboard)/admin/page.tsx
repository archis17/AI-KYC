'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import api from '@/lib/api'
import { KYCApplication } from '@/types'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'

export default function AdminPage() {
  const router = useRouter()
  const [applications, setApplications] = useState<KYCApplication[]>([])
  const [loading, setLoading] = useState(true)
  const [statusFilter, setStatusFilter] = useState<string>('')

  useEffect(() => {
    const token = localStorage.getItem('access_token')
    if (!token) {
      router.push('/login')
      return
    }

    fetchApplications()
  }, [router, statusFilter])

  const fetchApplications = async () => {
    try {
      const params = statusFilter ? { status: statusFilter } : {}
      const response = await api.get('/api/admin/applications', { params })
      setApplications(response.data)
    } catch (error) {
      console.error('Failed to fetch applications:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleApprove = async (id: number) => {
    try {
      await api.post(`/api/admin/applications/${id}/approve`)
      await fetchApplications()
    } catch (error) {
      console.error('Failed to approve:', error)
      alert('Failed to approve application')
    }
  }

  const handleReject = async (id: number) => {
    const reason = prompt('Enter rejection reason:')
    if (!reason) return

    try {
      await api.post(`/api/admin/applications/${id}/reject`, null, {
        params: { reason },
      })
      await fetchApplications()
    } catch (error) {
      console.error('Failed to reject:', error)
      alert('Failed to reject application')
    }
  }

  const getStatusBadge = (status: string) => {
    const variants: Record<string, "default" | "secondary" | "destructive" | "success" | "warning"> = {
      approved: 'success',
      rejected: 'destructive',
      review: 'warning',
      processing: 'secondary',
      pending: 'default',
    }
    return <Badge variant={variants[status] || 'default'}>{status}</Badge>
  }

  if (loading) {
    return <div className="text-center py-12">Loading...</div>
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Admin Dashboard</h1>
          <p className="text-muted-foreground mt-2">Manage all KYC applications</p>
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Filters</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex gap-4">
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="h-10 rounded-md border border-input bg-background px-3 py-2 text-sm"
            >
              <option value="">All Statuses</option>
              <option value="pending">Pending</option>
              <option value="processing">Processing</option>
              <option value="review">Review</option>
              <option value="approved">Approved</option>
              <option value="rejected">Rejected</option>
            </select>
          </div>
        </CardContent>
      </Card>

      <div className="grid gap-4">
        {applications.map((app) => (
          <Card key={app.id}>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>Application #{app.id}</CardTitle>
                  <CardDescription>
                    User ID: {app.user_id} | Created {new Date(app.created_at).toLocaleDateString()}
                  </CardDescription>
                </div>
                {getStatusBadge(app.status)}
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div>
                  <p className="text-sm">
                    <span className="font-medium">Documents:</span> {app.documents?.length || 0}
                  </p>
                  {app.risk_score && (
                    <p className="text-sm">
                      <span className="font-medium">Risk Score:</span> {app.risk_score.score.toFixed(1)}/100
                      {' '}({app.risk_score.decision})
                    </p>
                  )}
                </div>
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => router.push(`/dashboard/applications/${app.id}`)}
                  >
                    View Details
                  </Button>
                  {app.status === 'review' && (
                    <>
                      <Button
                        variant="default"
                        size="sm"
                        onClick={() => handleApprove(app.id)}
                      >
                        Approve
                      </Button>
                      <Button
                        variant="destructive"
                        size="sm"
                        onClick={() => handleReject(app.id)}
                      >
                        Reject
                      </Button>
                    </>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {applications.length === 0 && (
        <Card>
          <CardContent className="py-12 text-center">
            <p className="text-muted-foreground">No applications found</p>
          </CardContent>
        </Card>
      )}
    </div>
  )
}

