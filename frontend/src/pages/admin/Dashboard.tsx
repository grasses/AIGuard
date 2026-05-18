
import { useEffect, useState } from 'react';
import { Card, Row, Col, Statistic, Spin } from 'antd';
import { ApiOutlined, StopOutlined, TeamOutlined, UserOutlined } from '@ant-design/icons';
import { useTranslation } from 'react-i18next';
import { dashboardApi } from '../../api/dashboard';
import type { DashboardStats } from '../../types';

export default function AdminDashboard() {
  const { t } = useTranslation();
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    dashboardApi.adminStats().then((res) => setStats(res.data.data)).finally(() => setLoading(false));
  }, []);

  if (loading) return <Spin size="large" style={{ display: 'block', margin: '100px auto' }} />;

  return (
    <div>
      <h2 className="page-header">{t('nav.dashboard')}</h2>
      <Row gutter={[16, 16]}>
        <Col xs={24} sm={12} lg={6}><Card><Statistic title={t('dashboard.totalRequests24h')} value={stats?.total_requests_24h || 0} prefix={<ApiOutlined />} /></Card></Col>
        <Col xs={24} sm={12} lg={6}><Card><Statistic title={t('dashboard.blockedRequests24h')} value={stats?.blocked_requests_24h || 0} prefix={<StopOutlined />} /></Card></Col>
        <Col xs={24} sm={12} lg={6}><Card><Statistic title={t('dashboard.totalUsers')} value={stats?.total_users || 0} prefix={<TeamOutlined />} /></Card></Col>
        <Col xs={24} sm={12} lg={6}><Card><Statistic title={t('dashboard.activeUsers24h')} value={stats?.active_users_24h || 0} prefix={<UserOutlined />} /></Card></Col>
      </Row>
    </div>
  );
}
