
import { useEffect, useState } from 'react';
import { Card, Row, Col, Statistic, Spin } from 'antd';
import {
  ApiOutlined, StopOutlined, ThunderboltOutlined,
  FileTextOutlined, DollarOutlined,
} from '@ant-design/icons';
import { useTranslation } from 'react-i18next';
import { dashboardApi } from '../../api/dashboard';
import type { DashboardStats } from '../../types';

export default function Dashboard() {
  const { t } = useTranslation();
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    dashboardApi.userStats().then((res) => {
      setStats(res.data.data);
    }).finally(() => setLoading(false));
  }, []);

  if (loading) return <Spin size="large" style={{ display: 'block', margin: '100px auto' }} />;

  return (
    <div>
      <h2 className="page-header">{t('nav.dashboard')}</h2>
      <Row gutter={[16, 16]}>
        <Col xs={24} sm={12} lg={8}>
          <Card><Statistic title={t('dashboard.totalRequests24h')} value={stats?.total_requests_24h || 0} prefix={<ApiOutlined />} /></Card>
        </Col>
        <Col xs={24} sm={12} lg={8}>
          <Card><Statistic title={t('dashboard.blockedRequests24h')} value={stats?.blocked_requests_24h || 0} prefix={<StopOutlined />} /></Card>
        </Col>
        <Col xs={24} sm={12} lg={8}>
          <Card><Statistic title={t('dashboard.blockRate24h')} value={stats?.block_rate_24h || 0} suffix="%" precision={1} /></Card>
        </Col>
        <Col xs={24} sm={12} lg={8}>
          <Card><Statistic title={t('dashboard.avgLatency24h')} value={stats?.avg_latency_ms_24h || 0} suffix="ms" prefix={<ThunderboltOutlined />} /></Card>
        </Col>
        <Col xs={24} sm={12} lg={8}>
          <Card><Statistic title={t('dashboard.totalTokens24h')} value={stats?.total_tokens_24h || 0} prefix={<FileTextOutlined />} /></Card>
        </Col>
        <Col xs={24} sm={12} lg={8}>
          <Card><Statistic title={t('dashboard.pointsConsumed24h')} value={stats?.points_consumed_24h || 0} prefix={<DollarOutlined />} /></Card>
        </Col>
      </Row>
    </div>
  );
}
