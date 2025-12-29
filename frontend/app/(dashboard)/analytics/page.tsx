'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { motion } from 'framer-motion'
import { getAnalytics } from '@/lib/api'
import api from '@/lib/api'
import { AnalyticsResponse, User } from '@/types'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { 
  PieChart, 
  Pie, 
  Cell, 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  Legend, 
  ResponsiveContainer,
  LineChart,
  Line,
  AreaChart,
  Area
} from 'recharts'
import { Download, Calendar, TrendingUp, Users, CheckCircle, XCircle, Clock, AlertCircle } from 'lucide-react'

const COLORS = {
  approved: '#10b981',
  rejected: '#ef4444',
  review: '#f59e0b',
  pending: '#6b7280',
  processing: '#3b82f6',
}

const RISK_COLORS = {
  '0-30': '#10b981',
  '31-60': '#f59e0b',
  '61-100': '#ef4444',
}

export default function AnalyticsPage() {
  const router = useRouter()
  const [analytics, setAnalytics] = useState<AnalyticsResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [startDate, setStartDate] = useState('')
  const [endDate, setEndDate] = useState('')
  const [user, setUser] = useState<User | null>(null)

  useEffect(() => {
    const token = localStorage.getItem('access_token')
    if (!token) {
      router.push('/login')
      return
    }
    
    // Check if user is admin
    const checkUser = async () => {
      try {
        const response = await api.get('/api/auth/me')
        const userData = response.data
        setUser(userData)
        if (userData.role !== 'admin') {
          router.push('/dashboard')
          return
        }
        fetchAnalytics()
      } catch (error) {
        console.error('Failed to fetch user:', error)
        router.push('/login')
      }
    }
    
    checkUser()
  }, [router])

  const fetchAnalytics = async () => {
    try {
      setLoading(true)
      const data = await getAnalytics(startDate || undefined, endDate || undefined)
      setAnalytics(data)
    } catch (error) {
      console.error('Failed to fetch analytics:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleDateFilter = () => {
    fetchAnalytics()
  }

  const handleResetDates = () => {
    setStartDate('')
    setEndDate('')
    setTimeout(() => fetchAnalytics(), 100)
  }

  const exportToCSV = () => {
    if (!analytics) return

    const csvRows = []
    
    // Summary
    csvRows.push('Analytics Summary')
    csvRows.push(`Total Applications,${analytics.summary.total_applications}`)
    csvRows.push(`Approved,${analytics.summary.approved_count}`)
    csvRows.push(`Rejected,${analytics.summary.rejected_count}`)
    csvRows.push(`Review,${analytics.summary.review_count}`)
    csvRows.push(`Approval Rate,${analytics.summary.approval_rate}%`)
    csvRows.push(`Average Risk Score,${analytics.summary.average_risk_score || 'N/A'}`)
    csvRows.push('')
    
    // Status Distribution
    csvRows.push('Status Distribution')
    csvRows.push('Status,Count,Percentage')
    analytics.status_distribution.forEach(s => {
      csvRows.push(`${s.status},${s.count},${s.percentage}%`)
    })
    csvRows.push('')
    
    // Time Series
    csvRows.push('Applications Over Time')
    csvRows.push('Date,Total,Approved,Rejected,Review')
    analytics.applications_over_time.forEach(t => {
      csvRows.push(`${t.date},${t.count},${t.approved},${t.rejected},${t.review}`)
    })
    
    const csvContent = csvRows.join('\n')
    const blob = new Blob([csvContent], { type: 'text/csv' })
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `kyc-analytics-${new Date().toISOString().split('T')[0]}.csv`
    a.click()
    window.URL.revokeObjectURL(url)
  }

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="h-8 w-64 bg-gray-200 rounded animate-pulse" />
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="h-32 bg-gray-200 rounded-lg animate-pulse" />
          ))}
        </div>
      </div>
    )
  }

  if (!analytics) {
    return <div className="text-center py-12">No analytics data available</div>
  }

  const { summary } = analytics

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="space-y-6"
    >
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Analytics Dashboard</h1>
          <p className="text-muted-foreground mt-2">Comprehensive insights and metrics</p>
        </div>
        <Button onClick={exportToCSV} variant="outline">
          <Download className="w-4 h-4 mr-2" />
          Export CSV
        </Button>
      </div>

      {/* Date Filters */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Calendar className="w-5 h-5" />
            Date Range Filter
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex gap-4 items-end">
            <div className="flex-1">
              <label className="text-sm font-medium mb-2 block">Start Date</label>
              <Input
                type="date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
              />
            </div>
            <div className="flex-1">
              <label className="text-sm font-medium mb-2 block">End Date</label>
              <Input
                type="date"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
              />
            </div>
            <div className="flex gap-2">
              <Button onClick={handleDateFilter}>Apply Filter</Button>
              <Button onClick={handleResetDates} variant="outline">Reset</Button>
            </div>
          </div>
          <p className="text-sm text-muted-foreground mt-2">
            Period: {new Date(analytics.period_start).toLocaleDateString()} - {new Date(analytics.period_end).toLocaleDateString()}
          </p>
        </CardContent>
      </Card>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Applications</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{summary.total_applications}</div>
            <p className="text-xs text-muted-foreground">
              {summary.applications_today} today • {summary.applications_this_month} this month
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Approval Rate</CardTitle>
            <CheckCircle className="h-4 w-4 text-green-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{summary.approval_rate}%</div>
            <p className="text-xs text-muted-foreground">
              {summary.approved_count} approved out of {summary.approved_count + summary.rejected_count} completed
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Average Risk Score</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {summary.average_risk_score !== null ? summary.average_risk_score.toFixed(1) : 'N/A'}
            </div>
            <p className="text-xs text-muted-foreground">
              {summary.review_count} applications in review
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Avg Processing Time</CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {summary.average_processing_time_hours !== null 
                ? `${summary.average_processing_time_hours.toFixed(1)}h`
                : 'N/A'}
            </div>
            <p className="text-xs text-muted-foreground">
              {summary.processing_count} currently processing
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Status Distribution Chart */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Status Distribution</CardTitle>
            <CardDescription>Breakdown of application statuses</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={analytics.status_distribution}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ status, percentage }) => `${status}: ${percentage}%`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="count"
                >
                  {analytics.status_distribution.map((entry, index) => (
                    <Cell 
                      key={`cell-${index}`} 
                      fill={COLORS[entry.status as keyof typeof COLORS] || '#8884d8'} 
                    />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Risk Score Distribution</CardTitle>
            <CardDescription>Applications by risk score ranges</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={analytics.risk_score_distribution}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="range" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="count">
                  {analytics.risk_score_distribution.map((entry, index) => (
                    <Cell 
                      key={`cell-${index}`} 
                      fill={RISK_COLORS[entry.range as keyof typeof RISK_COLORS] || '#8884d8'} 
                    />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {/* Applications Over Time */}
      <Card>
        <CardHeader>
          <CardTitle>Applications Over Time</CardTitle>
          <CardDescription>Daily application trends</CardDescription>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={400}>
            <AreaChart data={analytics.applications_over_time}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis 
                dataKey="date" 
                tickFormatter={(value) => new Date(value).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
              />
              <YAxis />
              <Tooltip 
                labelFormatter={(value) => new Date(value).toLocaleDateString()}
              />
              <Legend />
              <Area 
                type="monotone" 
                dataKey="count" 
                stackId="1" 
                stroke="#3b82f6" 
                fill="#3b82f6" 
                name="Total"
              />
              <Area 
                type="monotone" 
                dataKey="approved" 
                stackId="2" 
                stroke="#10b981" 
                fill="#10b981" 
                name="Approved"
              />
              <Area 
                type="monotone" 
                dataKey="rejected" 
                stackId="3" 
                stroke="#ef4444" 
                fill="#ef4444" 
                name="Rejected"
              />
              <Area 
                type="monotone" 
                dataKey="review" 
                stackId="4" 
                stroke="#f59e0b" 
                fill="#f59e0b" 
                name="Review"
              />
            </AreaChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      {/* Document Type Stats and Rejection Reasons */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Document Type Statistics</CardTitle>
            <CardDescription>Upload and OCR confidence by document type</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {analytics.document_type_stats.map((stat) => (
                <div key={stat.document_type} className="flex items-center justify-between">
                  <div className="flex-1">
                    <p className="font-medium capitalize">
                      {stat.document_type.replace('_', ' ')}
                    </p>
                    <p className="text-sm text-muted-foreground">
                      {stat.count} documents
                    </p>
                  </div>
                  <div className="text-right">
                    {stat.average_ocr_confidence !== null && (
                      <p className="font-medium">
                        {stat.average_ocr_confidence.toFixed(1)}% OCR
                      </p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Top Rejection Reasons</CardTitle>
            <CardDescription>Most common reasons for application rejection</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {analytics.rejection_reasons.length > 0 ? (
                analytics.rejection_reasons.map((reason, index) => (
                  <div key={index} className="flex items-center justify-between">
                    <div className="flex-1">
                      <p className="font-medium">{reason.reason}</p>
                      <p className="text-sm text-muted-foreground">
                        {reason.count} applications ({reason.percentage}%)
                      </p>
                    </div>
                  </div>
                ))
              ) : (
                <p className="text-muted-foreground text-center py-4">
                  No rejection data available
                </p>
              )}
            </div>
          </CardContent>
        </Card>
      </div>
    </motion.div>
  )
}

