import { useEffect, useState } from 'react';
import { Card, Table, Tag, Switch, Button, Space, Input, Tabs, Popconfirm, message, Drawer, Typography } from 'antd';
import { PlusOutlined, SearchOutlined, EditOutlined, DeleteOutlined, ApiOutlined, CodeOutlined, LinkOutlined } from '@ant-design/icons';
import { useNavigate, useSearchParams, useLocation } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { assetsApi } from '../../../api/assets';
import { authApi } from '../../../api/auth';
import { useAuthStore } from '../../../stores/authStore';
import type { Asset } from '../../../types';

const { Text, Paragraph, Title } = Typography;

export default function AssetList() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const location = useLocation();
  const basePath = location.pathname.startsWith('/admin') ? '/admin' : '/user';
  const [searchParams, setSearchParams] = useSearchParams();
  const [assets, setAssets] = useState<Asset[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const activeTab = searchParams.get('tab') || 'llm';

  // Access drawer state
  const [accessDrawer, setAccessDrawer] = useState(false);
  const [selectedAsset, setSelectedAsset] = useState<Asset | null>(null);
  const [apiKey, setApiKey] = useState<string | null>(null);
  const user = useAuthStore((s) => s.user);

  const fetchAssets = async () => {
    setLoading(true);
    try {
      const res = await assetsApi.list({ type: activeTab, page, page_size: 20, search });
      setAssets(res.data.data.items);
      setTotal(res.data.data.total);
    } finally { setLoading(false); }
  };

  useEffect(() => { fetchAssets(); }, [activeTab, page, search]);

  const handleToggle = async (id: string, enabled: boolean) => {
    await assetsApi.toggle(id, enabled);
    fetchAssets();
  };

  const handleDelete = async (id: string) => {
    await assetsApi.delete(id);
    message.success(t('common.deleteSuccess'));
    fetchAssets();
  };

  const handleTest = async (id: string) => {
    const res = await assetsApi.test(id);
    const d = res.data.data;
    if (d.success) message.success(`OK — ${d.latency_ms}ms`);
    else message.error(d.message);
  };

  const openAccessDrawer = async (asset: Asset) => {
    setSelectedAsset(asset);
    setAccessDrawer(true);
    try {
      const res = await authApi.listApiKeys();
      const keys = res.data.data;
      if (keys.length > 0) {
        setApiKey(keys[0].key_prefix + '...');
      }
    } catch {
      setApiKey(null);
    }
  };

  const connectivityColor = (c: string) => c === 'healthy' ? 'green' : c === 'unhealthy' ? 'red' : 'default';

  // Build gateway URL for display
  const gatewayBaseUrl = window.location.origin + '/v1';

  const llmColumns = [
    { title: t('assets.name'), dataIndex: 'name', key: 'name', width: 150,
      render: (text: string, r: Asset) => (
        <a onClick={() => navigate(`${basePath}/assets/${r.id}/edit?type=${activeTab}`)}>{text}</a>
      )},
    { title: t('assets.provider'), dataIndex: 'provider', key: 'provider', width: 100,
      render: (v: string) => v ? <Tag>{v}</Tag> : '-' },
    { title: t('assets.modelNames'), dataIndex: 'model_names', key: 'models', width: 180,
      render: (v: string[]) => v ? (
        <Space size={2} wrap>{v.map((m, i) => <Tag key={i} color="blue">{m}</Tag>)}</Space>
      ) : '-' },
    { title: 'Endpoint', key: 'endpoint', width: 140,
      render: (_: any, r: Asset) => (
        <Text code copyable style={{ fontSize: 12 }}>{r.base_url?.replace(/\/+$/, '') || '-'}</Text>
      )},
    { title: t('assets.connectivity'), key: 'connectivity', width: 90,
      render: (_: any, r: Asset) => <Tag color={connectivityColor(r.connectivity)}>{r.connectivity}</Tag> },
    { title: t('assets.enabled'), key: 'enabled', width: 70,
      render: (_: any, r: Asset) => <Switch checked={r.enabled} onChange={(v) => handleToggle(r.id, v)} size="small" /> },
    { title: t('common.actions'), key: 'actions', width: 220,
      render: (_: any, r: Asset) => (
        <Space size={4}>
          <Button size="small" icon={<CodeOutlined />} type="primary" ghost
            onClick={() => openAccessDrawer(r)}>
            {t('assets.accessExample')}
          </Button>
          <Button size="small" icon={<ApiOutlined />} onClick={() => handleTest(r.id)} />
          <Button size="small" icon={<EditOutlined />}
            onClick={() => navigate(`${basePath}/assets/${r.id}/edit?type=${activeTab}`)} />
          <Popconfirm title={t('common.confirmDelete')} onConfirm={() => handleDelete(r.id)}>
            <Button size="small" danger icon={<DeleteOutlined />} />
          </Popconfirm>
        </Space>
      )},
  ];

  const defaultColumns = [
    { title: t('assets.name'), dataIndex: 'name', key: 'name',
      render: (text: string, r: Asset) => (
        <a onClick={() => navigate(`${basePath}/assets/${r.id}/edit?type=${activeTab}`)}>{text}</a>
      )},
    { title: t('assets.type'), dataIndex: 'type', key: 'type',
      render: (t: string) => <Tag className={`color-tag-${t}`}>{t.toUpperCase()}</Tag> },
    { title: t('assets.provider'), dataIndex: 'provider', key: 'provider', render: (v: string) => v || '-' },
    { title: t('assets.connectivity'), key: 'connectivity',
      render: (_: any, r: Asset) => <Tag color={connectivityColor(r.connectivity)}>{r.connectivity}</Tag> },
    { title: t('assets.enabled'), key: 'enabled',
      render: (_: any, r: Asset) => <Switch checked={r.enabled} onChange={(v) => handleToggle(r.id, v)} size="small" /> },
    { title: t('assets.createdAt'), dataIndex: 'created_at', key: 'created_at',
      render: (v: string) => v?.slice(0, 16) || '-' },
    { title: t('common.actions'), key: 'actions',
      render: (_: any, r: Asset) => (
        <Space>
          <Button size="small" icon={<ApiOutlined />} onClick={() => handleTest(r.id)}>{t('common.test')}</Button>
          <Button size="small" icon={<EditOutlined />}
            onClick={() => navigate(`${basePath}/assets/${r.id}/edit?type=${activeTab}`)} />
          <Popconfirm title={t('common.confirmDelete')} onConfirm={() => handleDelete(r.id)}>
            <Button size="small" danger icon={<DeleteOutlined />} />
          </Popconfirm>
        </Space>
      )},
  ];

  const columns = activeTab === 'llm' ? llmColumns : defaultColumns;

  return (
    <div>
      <h2 className="page-header">{t('nav.assets')}</h2>
      <Card>
        <Space style={{ marginBottom: 16, width: '100%', justifyContent: 'space-between' }}>
          <Tabs
            activeKey={activeTab}
            onChange={(key) => { setSearchParams({ tab: key }); setPage(1); }}
            items={[
              { key: 'llm', label: t('assets.llm') },
              { key: 'mcp', label: t('assets.mcp') },
              { key: 'memory', label: t('assets.memory') },
            ]}
          />
          <Space>
            <Input prefix={<SearchOutlined />} placeholder={t('common.search')} value={search}
              onChange={(e) => { setSearch(e.target.value); setPage(1); }} allowClear />
            <Button type="primary" icon={<PlusOutlined />}
              onClick={() => navigate(`${basePath}/assets/create?type=${activeTab}`)}>
              {t('common.create')}
            </Button>
          </Space>
        </Space>
        <Table columns={columns} dataSource={assets} rowKey="id" loading={loading}
          pagination={{ current: page, total, pageSize: 20, onChange: setPage }}
          size="small" scroll={{ x: activeTab === 'llm' ? 1100 : 800 }} />
      </Card>

      {/* Access Example Drawer */}
      <Drawer
        title={<Space><LinkOutlined /> {selectedAsset?.name} — {t('assets.accessExample')}</Space>}
        open={accessDrawer}
        onClose={() => setAccessDrawer(false)}
        width={680}
        extra={
          <Button type="primary" ghost icon={<EditOutlined />}
            onClick={() => {
              setAccessDrawer(false);
              navigate(`${basePath}/assets/${selectedAsset?.id}/edit?type=llm`);
            }}>
            {t('common.edit')}
          </Button>
        }
      >
        {selectedAsset && (() => {
          const models = selectedAsset.model_names || [];
          const firstModel = models[0] || selectedAsset.name;

          const curlExample = `curl -X POST ${gatewayBaseUrl}/chat/completions \\
  -H "Authorization: Bearer YOUR_API_KEY" \\
  -H "Content-Type: application/json" \\
  -d '{
    "model": "${firstModel}",
    "messages": [
      {"role": "system", "content": "You are a helpful assistant."},
      {"role": "user", "content": "Hello!"}
    ]${selectedAsset.max_tokens ? `,\n    "max_tokens": ${selectedAsset.max_tokens}` : ''}${selectedAsset.temperature !== undefined ? `,\n    "temperature": ${selectedAsset.temperature}` : ''}
  }'`;

          const pythonExample = `import openai

client = openai.OpenAI(
    base_url="${gatewayBaseUrl}",
    api_key="YOUR_API_KEY",
)

response = client.chat.completions.create(
    model="${firstModel}",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello!"},
    ],${selectedAsset.max_tokens ? `\n    max_tokens=${selectedAsset.max_tokens},` : ''}${selectedAsset.temperature !== undefined ? `\n    temperature=${selectedAsset.temperature},` : ''}
)

print(response.choices[0].message.content)`;

          const jsExample = `const response = await fetch("${gatewayBaseUrl}/chat/completions", {
  method: "POST",
  headers: {
    "Authorization": "Bearer YOUR_API_KEY",
    "Content-Type": "application/json",
  },
  body: JSON.stringify({
    model: "${firstModel}",
    messages: [
      { role: "system", content: "You are a helpful assistant." },
      { role: "user", content: "Hello!" },${selectedAsset.max_tokens ? `\n      { max_tokens: ${selectedAsset.max_tokens} },` : ''}
    ],${selectedAsset.temperature !== undefined ? `\n    temperature: ${selectedAsset.temperature},` : ''}
  }),
});

const data = await response.json();
console.log(data.choices[0].message.content);`;

          return (
            <div>
              {/* Asset Info Card */}
              <Card size="small" style={{ marginBottom: 16, background: '#fafafa' }}>
                <Space direction="vertical" size={4}>
                  <Text strong>{t('assets.name')}: {selectedAsset.name}</Text>
                  <Text>Provider: <Tag>{selectedAsset.provider}</Tag></Text>
                  <Text>Base URL: <Text code copyable>{selectedAsset.base_url}</Text></Text>
                  <Text>{t('assets.modelNames')}:{' '}
                    {(selectedAsset.model_names || []).map((m, i) => (
                      <Tag key={i} color="blue" style={{ cursor: 'pointer' }}>{m}</Tag>
                    ))}
                  </Text>
                </Space>
              </Card>

              {/* Gateway Endpoint */}
              <Title level={5}><LinkOutlined /> Gateway Endpoint</Title>
              <Paragraph>
                <Text code copyable style={{ fontSize: 14 }}>
                  {gatewayBaseUrl}/chat/completions
                </Text>
              </Paragraph>
              <Paragraph type="secondary">
                {t('assets.gatewayNote', '所有请求经AI Firewall网关转发，自动执行护栏检测链。使用API Key认证。')}
              </Paragraph>

              {/* API Key hint */}
              <Card size="small" style={{ marginBottom: 16, background: '#fff7e6', border: '1px solid #ffd591' }}>
                <Text>
                  🔑 {t('assets.apiKeyNote', '在')}{' '}
                  <a onClick={() => { setAccessDrawer(false); navigate('/user/billing'); }}>
                    {t('nav.apiKeys')}
                  </a>
                  {' '}{t('assets.apiKeyNote2', '中创建API Key，替换下方示例中的 YOUR_API_KEY')}
                </Text>
              </Card>

              {/* cURL Example */}
              <Title level={5}>cURL</Title>
              <pre style={{
                background: '#1e1e1e', color: '#d4d4d4', padding: 16,
                borderRadius: 8, fontSize: 13, lineHeight: 1.6,
                overflowX: 'auto', whiteSpace: 'pre',
              }}>
                <code>{curlExample}</code>
              </pre>

              {/* Python Example */}
              <Title level={5} style={{ marginTop: 20 }}>Python (OpenAI SDK)</Title>
              <pre style={{
                background: '#1e1e1e', color: '#d4d4d4', padding: 16,
                borderRadius: 8, fontSize: 13, lineHeight: 1.6,
                overflowX: 'auto', whiteSpace: 'pre',
              }}>
                <code>{pythonExample}</code>
              </pre>

              {/* JavaScript Example */}
              <Title level={5} style={{ marginTop: 20 }}>JavaScript (Fetch)</Title>
              <pre style={{
                background: '#1e1e1e', color: '#d4d4d4', padding: 16,
                borderRadius: 8, fontSize: 13, lineHeight: 1.6,
                overflowX: 'auto', whiteSpace: 'pre',
              }}>
                <code>{jsExample}</code>
              </pre>

              {/* Streaming Example */}
              <Title level={5} style={{ marginTop: 20 }}>Streaming (cURL)</Title>
              <pre style={{
                background: '#1e1e1e', color: '#d4d4d4', padding: 16,
                borderRadius: 8, fontSize: 13, lineHeight: 1.6,
                overflowX: 'auto', whiteSpace: 'pre',
              }}>
                <code>{`curl -X POST ${gatewayBaseUrl}/chat/completions \\
  -H "Authorization: Bearer YOUR_API_KEY" \\
  -H "Content-Type: application/json" \\
  -d '{
    "model": "${firstModel}",
    "messages": [{"role": "user", "content": "Hello!"}],
    "stream": true
  }'`}</code>
              </pre>
            </div>
          );
        })()}
      </Drawer>
    </div>
  );
}
