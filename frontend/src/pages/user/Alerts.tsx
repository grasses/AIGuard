
import { useEffect, useState } from 'react';
import { Card, Table, Tag, Button, Space, message, Tabs } from 'antd';
import { BellOutlined, CheckOutlined } from '@ant-design/icons';
import { useTranslation } from 'react-i18next';
import { alertsApi } from '../../api/alerts';
import type { AlertEvent } from '../../types';

export default function Alerts() {
  const { t } = useTranslation();
  const [events, setEvents] = useState<AlertEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<string>('all');

  const fetchEvents = async () => {
    setLoading(true);
    try {
      const params: any = {};
      if (activeTab === 'unread') params.is_read = false;
      else if (activeTab === 'read') params.is_read = true;
      const res = await alertsApi.listEvents(params);
      setEvents(res.data.data.items);
    } finally { setLoading(false); }
  };

  useEffect(() => { fetchEvents(); }, [activeTab]);

  const markAllRead = async () => {
    await alertsApi.markAllRead();
    message.success(t('alerts.markAllRead'));
    fetchEvents();
  };

  const levelColor = (l: string) => l === 'critical' ? 'red' : l === 'warning' ? 'orange' : 'blue';

  return (
    <div>
      <h2 className="page-header">{t('nav.alerts')}</h2>
      <Card>
        <Space style={{ marginBottom: 16 }}>
          <Tabs activeKey={activeTab} onChange={setActiveTab} items={[
            { key: 'all', label: t('alerts.all') },
            { key: 'unread', label: t('alerts.unread') },
          ]} />
          <Button icon={<CheckOutlined />} onClick={markAllRead}>{t('alerts.markAllRead')}</Button>
        </Space>
        <Table
          dataSource={events}
          rowKey="id"
          loading={loading}
          columns={[
            { title: t('alerts.level'), dataIndex: 'level', key: 'level', width: 80, render: (l: string) => <Tag color={levelColor(l)}>{l}</Tag> },
            { title: t('alerts.title'), dataIndex: 'title', key: 'title', render: (t: string, r: AlertEvent) => (
              <span style={{ fontWeight: r.is_read ? 'normal' : 'bold' }}>{t}</span>
            )},
            { title: t('alerts.message'), dataIndex: 'message', key: 'message', ellipsis: true },
            { title: t('alerts.time'), dataIndex: 'created_at', key: 'time', width: 160, render: (v: string) => v?.slice(0, 16) || '-' },
          ]}
          size="middle"
        />
      </Card>
    </div>
  );
}
