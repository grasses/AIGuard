import { useEffect, useState } from 'react';
import { Card, Table, Button, Space, Modal, Input, message, Tag, Typography, Popconfirm, Alert } from 'antd';
import { PlusOutlined, CopyOutlined, KeyOutlined, DeleteOutlined, EyeOutlined } from '@ant-design/icons';
import { useTranslation } from 'react-i18next';
import { authApi } from '../../api/auth';
import type { ApiKey } from '../../types';

const { Text, Paragraph } = Typography;

export default function ApiKeys() {
  const { t } = useTranslation();
  const [keys, setKeys] = useState<ApiKey[]>([]);
  const [loading, setLoading] = useState(false);
  const [createOpen, setCreateOpen] = useState(false);
  const [newKeyName, setNewKeyName] = useState('');
  const [creating, setCreating] = useState(false);

  // The raw key is only shown once after creation
  const [rawKey, setRawKey] = useState<string | null>(null);
  const [showRawKey, setShowRawKey] = useState(false);
  const [copiedKey, setCopiedKey] = useState(false);

  const fetchKeys = async () => {
    setLoading(true);
    try {
      const res = await authApi.listApiKeys();
      setKeys(res.data.data || []);
    } catch {
      message.error('Failed to load API keys');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchKeys(); }, []);

  const handleCreate = async () => {
    if (!newKeyName.trim()) {
      message.warning('Please enter a name for the API key');
      return;
    }
    setCreating(true);
    try {
      const res = await authApi.createApiKey(newKeyName.trim());
      const { raw_key } = res.data.data;
      setRawKey(raw_key);
      setShowRawKey(true);
      setCreateOpen(false);
      setNewKeyName('');
      fetchKeys();
    } catch (err: any) {
      message.error(err.response?.data?.detail || 'Failed to create API key');
    } finally {
      setCreating(false);
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await authApi.deleteApiKey(id);
      message.success('API Key deleted');
      fetchKeys();
    } catch {
      message.error('Failed to delete API key');
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text).then(() => {
      message.success('Copied to clipboard');
      setCopiedKey(true);
    });
  };

  // Mask raw key for display: show prefix and suffix
  const maskKey = (key: string) => {
    if (key.length <= 16) return key;
    return key.slice(0, 10) + '••••••••••••••••' + key.slice(-4);
  };

  const columns = [
    {
      title: t('assets.name', 'Name'),
      dataIndex: 'name',
      key: 'name',
      render: (name: string) => <Text strong><KeyOutlined /> {name}</Text>,
    },
    {
      title: 'API Key',
      dataIndex: 'key_prefix',
      key: 'key_prefix',
      width: 220,
      render: (prefix: string) => (
        <Text code style={{ fontSize: 13 }}>{prefix}••••••••••••••••••••</Text>
      ),
    },
    {
      title: t('common.status', 'Status'),
      dataIndex: 'enabled',
      key: 'enabled',
      width: 90,
      render: (enabled: boolean) => (
        <Tag color={enabled ? 'green' : 'red'}>{enabled ? 'Active' : 'Disabled'}</Tag>
      ),
    },
    {
      title: t('common.createdAt', 'Created'),
      dataIndex: 'created_at',
      key: 'created_at',
      width: 160,
      render: (v: string) => v?.slice(0, 16) || '-',
    },
    {
      title: 'Last Used',
      dataIndex: 'last_used_at',
      key: 'last_used_at',
      width: 160,
      render: (v: string) => v ? v.slice(0, 16) : <Text type="secondary">Never</Text>,
    },
    {
      title: t('common.actions', 'Actions'),
      key: 'actions',
      width: 80,
      render: (_: any, r: ApiKey) => (
        <Popconfirm
          title="Delete this API key?"
          description="Any application using this key will lose access."
          onConfirm={() => handleDelete(r.id)}
          okText="Delete"
          cancelText="Cancel"
        >
          <Button size="small" danger icon={<DeleteOutlined />} />
        </Popconfirm>
      ),
    },
  ];

  return (
    <div>
      <h2 className="page-header">
        <KeyOutlined /> {t('nav.apiKeys', 'API Keys')}
      </h2>

      {/* Raw Key Display (shown only once after creation) */}
      {showRawKey && rawKey && (
        <Alert
          type="success"
          showIcon
          icon={<KeyOutlined />}
          message="API Key Created Successfully"
          description={
            <div>
              <Paragraph type="secondary" style={{ marginBottom: 8 }}>
                Copy this key now — it will <Text strong>not</Text> be shown again.
              </Paragraph>
              <Space>
                <Input.Password
                  value={rawKey}
                  readOnly
                  style={{ width: 420, fontFamily: 'monospace' }}
                  addonAfter={
                    <Button
                      type="link"
                      size="small"
                      icon={<CopyOutlined />}
                      onClick={() => copyToClipboard(rawKey)}
                      style={{ padding: 0 }}
                    />
                  }
                />
                <Button
                  type="primary"
                  size="small"
                  onClick={() => {
                    setShowRawKey(false);
                    setRawKey(null);
                    setCopiedKey(false);
                  }}
                >
                  {copiedKey ? 'Done' : 'I\'ve saved my key'}
                </Button>
              </Space>
            </div>
          }
          style={{ marginBottom: 24, borderRadius: 8 }}
          closable
          onClose={() => setShowRawKey(false)}
        />
      )}

      <Card
        extra={
          <Button type="primary" icon={<PlusOutlined />} onClick={() => setCreateOpen(true)}>
            Create API Key
          </Button>
        }
      >
        {/* Usage guide */}
        <Alert
          type="info"
          message="How to use API Keys"
          description={
            <div>
              <Paragraph style={{ marginBottom: 4 }}>
                Include the API Key in the <Text code>Authorization</Text> header of your requests:
              </Paragraph>
              <pre style={{
                background: '#1e1e1e', color: '#d4d4d4', padding: 12,
                borderRadius: 6, fontSize: 13, marginTop: 8,
              }}>
                <code>Authorization: Bearer YOUR_API_KEY</code>
              </pre>
              <Paragraph style={{ marginTop: 8, marginBottom: 0 }}>
                Example:{' '}
                <Text code copyable>
                  {`curl -H "Authorization: Bearer YOUR_API_KEY" ${window.location.origin}/v1/chat/completions`}
                </Text>
              </Paragraph>
            </div>
          }
          style={{ marginBottom: 24, borderRadius: 8 }}
        />

        <Table
          columns={columns}
          dataSource={keys}
          rowKey="id"
          loading={loading}
          size="middle"
          locale={{ emptyText: 'No API keys yet. Create one to access the /v1 gateway.' }}
        />
      </Card>

      {/* Create Modal */}
      <Modal
        title="Create API Key"
        open={createOpen}
        onOk={handleCreate}
        onCancel={() => { setCreateOpen(false); setNewKeyName(''); }}
        confirmLoading={creating}
        okText="Create"
      >
        <Input
          placeholder="Enter a name for this key (e.g., 'Production', 'Testing')"
          value={newKeyName}
          onChange={(e) => setNewKeyName(e.target.value)}
          onPressEnter={handleCreate}
          maxLength={100}
          prefix={<KeyOutlined />}
        />
      </Modal>
    </div>
  );
}
