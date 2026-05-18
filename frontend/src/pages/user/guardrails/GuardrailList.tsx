import { useEffect, useState } from 'react';
import { Card, Row, Col, Tag, Switch, Button, Space, Input, Select, Spin } from 'antd';
import { PlusOutlined, SearchOutlined, EditOutlined } from '@ant-design/icons';
import { useNavigate, useLocation } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { guardrailsApi } from '../../../api/guardrails';
import type { Guardrail } from '../../../types';

export default function GuardrailList() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const location = useLocation();
  const basePath = location.pathname.startsWith('/admin') ? '/admin' : '/user';
  const [guardrails, setGuardrails] = useState<Guardrail[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [domainFilter, setDomainFilter] = useState<string | undefined>();
  const [positionFilter, setPositionFilter] = useState<string | undefined>();

  const fetchData = async () => {
    setLoading(true);
    try {
      const res = await guardrailsApi.list({ search, domain: domainFilter, position: positionFilter });
      setGuardrails(res.data.data.items);
    } finally { setLoading(false); }
  };

  useEffect(() => { fetchData(); }, [search, domainFilter, positionFilter]);

  const handleToggle = async (id: string, enabled: boolean) => {
    await guardrailsApi.toggle(id, enabled);
    fetchData();
  };

  const domainColor = (d: string) => d === 'llm' ? 'blue' : d === 'mcp' ? 'green' : 'orange';
  const positionColor = (p: string) => p === 'pre' ? 'cyan' : 'purple';
  const actionColor = (a: string) => a === 'block' ? 'red' : a === 'correct' ? 'blue' : 'gold';

  return (
    <div>
      <h2 className="page-header">{t('nav.guardrails')}</h2>
      <Card>
        <Space style={{ marginBottom: 16, width: '100%', justifyContent: 'space-between' }} wrap>
          <Space wrap>
            <Input prefix={<SearchOutlined />} placeholder={t('common.search')} value={search}
              onChange={(e) => setSearch(e.target.value)} allowClear style={{ width: 200 }} />
            <Select placeholder={t('guardrails.domain')} allowClear style={{ width: 120 }} onChange={setDomainFilter}>
              <Select.Option value="llm">LLM</Select.Option>
              <Select.Option value="mcp">MCP</Select.Option>
              <Select.Option value="memory">Memory</Select.Option>
            </Select>
            <Select placeholder={t('guardrails.position')} allowClear style={{ width: 120 }} onChange={setPositionFilter}>
              <Select.Option value="pre">{t('guardrails.pre')}</Select.Option>
              <Select.Option value="post">{t('guardrails.post')}</Select.Option>
            </Select>
          </Space>
          <Button type="primary" icon={<PlusOutlined />} onClick={() => navigate(`${basePath}/guardrails/create`)}>
            {t('guardrails.create')}
          </Button>
        </Space>

        <Spin spinning={loading}>
          <Row gutter={[16, 16]}>
            {guardrails.map((g) => (
              <Col xs={24} sm={12} lg={8} key={g.id}>
                <Card hoverable actions={[
                  <Switch key="toggle" checked={g.enabled} onChange={(v) => handleToggle(g.id, v)} />,
                  <Button key="edit" type="link" icon={<EditOutlined />}
                    onClick={() => navigate(`${basePath}/guardrails/${g.id}/edit`)}>{t('common.edit')}</Button>,
                ]}>
                  <Card.Meta
                    title={g.name}
                    description={<>
                      <Space size={4} wrap style={{ marginBottom: 8 }}>
                        <Tag color={domainColor(g.domain)}>{g.domain.toUpperCase()}</Tag>
                        <Tag color={positionColor(g.position)}>{t('guardrails.' + g.position)}</Tag>
                        <Tag>{g.guardrail_type}</Tag>
                      </Space>
                      <p style={{ color: '#666', fontSize: 13, marginBottom: 8 }}>
                        {g.description?.slice(0, 80)}{(g.description?.length || 0) > 80 ? '...' : ''}</p>
                      <Space size={4}>
                        <Tag color={actionColor(g.hit_action)}>{t('guardrails.' + g.hit_action)}</Tag>
                        {g.streaming_enabled && <Tag>Stream</Tag>}
                      </Space>
                    </>}
                  />
                </Card>
              </Col>
            ))}
          </Row>
          {!loading && guardrails.length === 0 && (
            <div style={{ textAlign: 'center', padding: 48, color: '#999' }}>{t('common.noData')}</div>
          )}
        </Spin>
      </Card>
    </div>
  );
}
