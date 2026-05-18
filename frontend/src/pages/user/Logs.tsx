
import { useEffect, useState } from 'react';
import { Card, Table, Tag, Button, Space, Input, Select, Drawer, Descriptions } from 'antd';
import { SearchOutlined, EyeOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { logsApi } from '../../api/logs';
import type { RequestLog, RequestLogDetail } from '../../types';

export default function Logs() {
  const { t } = useTranslation();
  const [logs, setLogs] = useState<RequestLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [detail, setDetail] = useState<RequestLogDetail | null>(null);
  const [drawerOpen, setDrawerOpen] = useState(false);

  const fetchLogs = async () => {
    setLoading(true);
    try {
      const res = await logsApi.list({ page_size: 50 });
      setLogs(res.data.data.items);
    } finally { setLoading(false); }
  };

  useEffect(() => { fetchLogs(); }, []);

  const viewDetail = async (id: string) => {
    const res = await logsApi.getDetail(id);
    setDetail(res.data.data);
    setDrawerOpen(true);
  };

  const statusColor = (s: string) => {
    if (s === 'completed') return 'green';
    if (s.startsWith('blocked')) return 'red';
    return 'orange';
  };

  return (
    <div>
      <h2 className="page-header">{t('nav.logs')}</h2>
      <Card>
        <Table
          dataSource={logs}
          rowKey="id"
          loading={loading}
          columns={[
            { title: 'Request ID', dataIndex: 'request_id', key: 'request_id', width: 150, ellipsis: true },
            { title: t('logs.model'), dataIndex: 'model', key: 'model', width: 120 },
            { title: t('logs.status'), dataIndex: 'status', key: 'status', width: 100, render: (s: string) => <Tag color={statusColor(s)}>{s}</Tag> },
            { title: t('logs.tokens'), key: 'tokens', width: 80, render: (_: any, r: RequestLog) => r.request_tokens + r.response_tokens },
            { title: t('logs.latency'), dataIndex: 'latency_ms', key: 'latency', width: 80, render: (v: number) => `${v}ms` },
            { title: t('logs.points'), dataIndex: 'points_consumed', key: 'points', width: 60 },
            { title: t('logs.time'), dataIndex: 'created_at', key: 'time', width: 160, render: (v: string) => v?.slice(0, 16) || '-' },
            { title: t('common.actions'), key: 'actions', width: 80, render: (_: any, r: RequestLog) => (
              <Button size="small" icon={<EyeOutlined />} onClick={() => viewDetail(r.id)} />
            )},
          ]}
          size="small"
          scroll={{ x: 900 }}
        />
      </Card>

      <Drawer title={t('logs.detail')} open={drawerOpen} onClose={() => setDrawerOpen(false)} width={640}>
        {detail && (
          <Descriptions column={1} bordered size="small">
            <Descriptions.Item label="Request ID">{detail.request_id}</Descriptions.Item>
            <Descriptions.Item label={t('logs.model')}>{detail.model}</Descriptions.Item>
            <Descriptions.Item label={t('logs.status')}><Tag color={statusColor(detail.status)}>{detail.status}</Tag></Descriptions.Item>
            <Descriptions.Item label={t('logs.latency')}>{detail.latency_ms}ms</Descriptions.Item>
            {detail.blocked_by && <Descriptions.Item label={t('logs.blockedBy')}>{detail.blocked_by}</Descriptions.Item>}
            {detail.block_reason && <Descriptions.Item label={t('logs.blockReason')}>{detail.block_reason}</Descriptions.Item>}
            <Descriptions.Item label={t('logs.responseContent')}>
              <pre style={{ maxHeight: 200, overflow: 'auto', fontSize: 12 }}>{detail.response_content || '-'}</pre>
            </Descriptions.Item>
          </Descriptions>
        )}
      </Drawer>
    </div>
  );
}
