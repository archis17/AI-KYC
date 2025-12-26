'use client'

import { useEffect, useMemo } from 'react'
import { useRouter } from 'next/navigation'
import { motion, AnimatePresence } from 'framer-motion'
import api from '@/lib/api'
import { KYCApplication } from '@/types'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import Link from 'next/link'
import { usePolling } from '@/hooks/usePolling'

export default function DashboardPage() {
  const router = useRouter()

  useEffect(() => {
    const token = localStorage.getItem('access_token')
    if (!token) {
      router.push('/login')
      return
    }
  }, [router])

  const fetchApplications = async () => {
    const response = await api.get('/api/kyc/applications')
    return response.data as KYCApplication[]
  }

  // Poll for updates if any applications are processing
  const { data: applicationsData, loading } = usePolling(
    fetchApplications,
    {
      enabled: true,
      interval: 3000,
    }
  )

  // Ensure applications is always an array
  const applications = applicationsData || []

  // Check if we should continue polling
  const hasProcessingApps = useMemo(() => {
    if (!applications || applications.length === 0) return false
    return applications.some(app => app.status === 'processing' || app.status === 'pending')
  }, [applications])

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
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <div className="h-8 w-48 bg-gray-200 rounded animate-pulse mb-2" />
            <div className="h-4 w-64 bg-gray-200 rounded animate-pulse" />
          </div>
          <div className="h-10 w-32 bg-gray-200 rounded animate-pulse" />
        </div>
        <div className="grid gap-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="border rounded-lg p-6 space-y-4">
              <div className="h-6 w-32 bg-gray-200 rounded animate-pulse" />
              <div className="h-4 w-48 bg-gray-200 rounded animate-pulse" />
              <div className="h-4 w-24 bg-gray-200 rounded animate-pulse" />
            </div>
          ))}
        </div>
      </div>
    )
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="space-y-6"
    >
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Dashboard</h1>
          <p className="text-muted-foreground mt-2">Manage your KYC applications</p>
        </div>
        <motion.div
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
        >
          <Button onClick={() => router.push('/dashboard/new')}>
            New Application
          </Button>
        </motion.div>
      </div>

      {applications.length === 0 ? (
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.3 }}
        >
          <Card>
            <CardContent className="py-12 text-center">
              <p className="text-muted-foreground mb-4">No applications yet</p>
              <Button onClick={() => router.push('/dashboard/new')}>
                Create Your First Application
              </Button>
            </CardContent>
          </Card>
        </motion.div>
      ) : (
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
                          Created {new Date(app.created_at).toLocaleDateString()}
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
                    <div className="space-y-2">
                      <p className="text-sm">
                        <span className="font-medium">Documents:</span> {app.documents?.length || 0}
                      </p>
                      {app.risk_score && (
                        <p className="text-sm">
                          <span className="font-medium">Risk Score:</span> {app.risk_score.score.toFixed(1)}/100
                        </p>
                      )}
                      {app.processing_message && app.status === 'processing' && (
                        <p className="text-xs text-muted-foreground italic">
                          {app.processing_message}
                        </p>
                      )}
                      <div className="pt-2">
                        <Link href={`/dashboard/applications/${app.id}`}>
                          <Button variant="outline" size="sm">View Details</Button>
                        </Link>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </motion.div>
            ))}
          </AnimatePresence>
        </div>
      )}
    </motion.div>
  )
}

