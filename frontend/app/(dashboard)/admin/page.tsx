'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { motion, AnimatePresence } from 'framer-motion'
import api, { deleteApplication } from '@/lib/api'
import { KYCApplication } from '@/types'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Dialog } from '@/components/ui/dialog'
import { useToast } from '@/components/ui/toast'

export default function AdminPage() {
  const router = useRouter()
  const [applications, setApplications] = useState<KYCApplication[]>([])
  const [loading, setLoading] = useState(true)
  const [statusFilter, setStatusFilter] = useState<string>('')
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false)
  const [applicationToDelete, setApplicationToDelete] = useState<number | null>(null)
  const { showToast } = useToast()

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
      showToast('Application approved successfully', 'success')
    } catch (error) {
      console.error('Failed to approve:', error)
      showToast('Failed to approve application', 'error')
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
      showToast('Application rejected successfully', 'success')
    } catch (error) {
      console.error('Failed to reject:', error)
      showToast('Failed to reject application', 'error')
    }
  }

  const handleDeleteClick = (id: number) => {
    setApplicationToDelete(id)
    setDeleteDialogOpen(true)
  }

  const handleDeleteConfirm = async () => {
    if (!applicationToDelete) return

    try {
      await deleteApplication(applicationToDelete)
      await fetchApplications()
      showToast('Application deleted successfully', 'success')
      setDeleteDialogOpen(false)
      setApplicationToDelete(null)
    } catch (error) {
      console.error('Failed to delete:', error)
      showToast('Failed to delete application', 'error')
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

  const appToDelete = applications.find(app => app.id === applicationToDelete)

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="space-y-6"
    >
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
        <AnimatePresence mode="popLayout">
          {applications.map((app, index) => (
            <motion.div
              key={app.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20, scale: 0.95 }}
              transition={{ duration: 0.3, delay: index * 0.05 }}
              layout
            >
              <Card className="hover:shadow-lg transition-shadow duration-200">
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <div>
                      <CardTitle>Application #{app.id}</CardTitle>
                      <CardDescription>
                        User ID: {app.user_id} | Created {new Date(app.created_at).toLocaleDateString()}
                      </CardDescription>
                    </div>
                    <motion.div
                      key={app.status}
                      initial={{ scale: 0.8, opacity: 0 }}
                      animate={{ scale: 1, opacity: 1 }}
                      transition={{ duration: 0.2 }}
                    >
                      {getStatusBadge(app.status)}
                    </motion.div>
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
                    <div className="flex gap-2 flex-wrap">
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
                      <Button
                        variant="destructive"
                        size="sm"
                        onClick={() => handleDeleteClick(app.id)}
                      >
                        Delete
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>

      {applications.length === 0 && (
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.3 }}
        >
          <Card>
            <CardContent className="py-12 text-center">
              <p className="text-muted-foreground">No applications found</p>
            </CardContent>
          </Card>
        </motion.div>
      )}

      <Dialog
        open={deleteDialogOpen}
        onOpenChange={setDeleteDialogOpen}
        title="Delete Application"
        description={`Are you sure you want to delete Application #${appToDelete?.id}? This action cannot be undone and will delete all associated documents, risk scores, and audit logs.`}
        confirmText="Delete"
        cancelText="Cancel"
        variant="destructive"
        onConfirm={handleDeleteConfirm}
        onCancel={() => {
          setDeleteDialogOpen(false)
          setApplicationToDelete(null)
        }}
      />
    </motion.div>
  )
}

