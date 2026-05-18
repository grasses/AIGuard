import { useEffect, useState } from 'react';
import { Card, Table, Tag, Switch, Button, Space, Popconfirm, message } from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons';
import { useNavigate, useLocation } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { trafficApi } from '../../../api/traffic';
import type { TrafficConfig } from '../../../types';

export default function TrafficConfigList() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const location = useLocation();
  const basePath = location.pathname.startsWith('/admin') ? '/admin' : '/user';
  const [configs, setConfigs] = useState<TrafficConfig[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchData = async () => {
    setLoading(true);
    try {
      const res = await trafficApi.list({});
      setConfigs(res.data.data.items);
    } finally { setLoading(false); }
  };

  useEffect(() => { fetchData(); }, []);

  const handleDelete = async (id: string) => {
    await trafficApi.delete(id);
    message.success(t('common.deleteSuccess'));
    fetchData();
  };

  const columns = [
    { title: t('traffic.name'), dataIndex: 'name', key: 'name', render: (text: string, r: TrafficConfig) => (
      <a onClick={() => navigate(`${basePath}/traffic-configs/${r.id}/edit`)}>{text}</a>
    )},
    { title: t('traffic.assets'), key: 'assets', render: (_: any, r: TrafficConfig) => (
      <Space size={4} wrap>{(r.assets_summary || []).map((a, i) => <Tag key={i}>{a.name}</Tag>)}</Space>
    )},
    { title: t('traffic.preGuardrails'), dataIndex: 'pre_guardrail_count', key: 'pre' },
    { title: t('traffic.postGuardrails'), dataIndex: 'post_guardrail_count', key: 'post' },
    { title: t('traffic.blockRate24h'), key: 'block_rate', render: (_: any, r: TrafficConfig) => (
      <span style={{ color: r.block_rate_24h > 10 ? 'red' : 'inherit' }}>{r.block_rate_24h}%</span>
    )},
    { title: t('common.enabled'), key: 'enabled', render: (_: any, r: TrafficConfig) => (
      <Switch checked={r.enabled} size="small" />
    )},
    { title: t('common.actions'), key: 'actions', render: (_: any, r: TrafficConfig) => (
      <Space>
        <Button size="small" icon={<EditOutlined />} onClick={() => navigate(`${basePath}/traffic-configs/${r.id}/edit`)} />
        <Popconfirm title={t('common.confirmDelete')} onConfirm={() => handleDelete(r.id)}>
          <Button size="small" danger icon={<DeleteOutlined />} />
        </Popconfirm>
      </Space>
    )},
  ];

  return (
    <div>
      <h2 className="page-header">{t('nav.trafficConfigs')}</h2>
      <Card extra={<Button type="primary" icon={<PlusOutlined />}
        onClick={() => navigate(`${basePath}/traffic-configs/create`)}>{t('common.create')}</Button>}>
        <Table columns={columns} dataSource={configs} rowKey="id" loading={loading} size="middle" />
      </Card>
    </div>
  );
}
