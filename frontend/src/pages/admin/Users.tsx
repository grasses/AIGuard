
import { useEffect, useState } from 'react';
import { Card, Table, Tag, Input, Select, Space } from 'antd';
import { SearchOutlined } from '@ant-design/icons';
import { useTranslation } from 'react-i18next';
import { usersApi } from '../../api/users';
import type { User } from '../../types';

export default function Users() {
  const { t } = useTranslation();
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');

  const fetchUsers = async () => {
    setLoading(true);
    try {
      const res = await usersApi.list({ search });
      setUsers(res.data.data.items);
    } finally { setLoading(false); }
  };

  useEffect(() => { fetchUsers(); }, [search]);

  const roleColor = (r: string) => r === 'super_admin' ? 'red' : r === 'admin' ? 'blue' : 'default';
  const statusColor = (s: string) => s === 'active' ? 'green' : s === 'locked' ? 'red' : 'orange';

  return (
    <div>
      <h2 className="page-header">{t('nav.userManagement')}</h2>
      <Card>
        <Space style={{ marginBottom: 16 }}>
          <Input prefix={<SearchOutlined />} value={search} onChange={(e) => setSearch(e.target.value)} placeholder={t('common.search')} />
        </Space>
        <Table
          dataSource={users}
          rowKey="id"
          loading={loading}
          columns={[
            { title: t('users.username'), dataIndex: 'username', key: 'username' },
            { title: t('users.email'), dataIndex: 'email', key: 'email' },
            { title: t('users.role'), dataIndex: 'role', key: 'role', render: (r: string) => <Tag color={roleColor(r)}>{r}</Tag> },
            { title: t('users.status'), dataIndex: 'status', key: 'status', render: (s: string) => <Tag color={statusColor(s)}>{s}</Tag> },
            { title: t('users.balance'), dataIndex: 'balance', key: 'balance' },
            { title: t('users.createdAt'), dataIndex: 'created_at', key: 'created_at', render: (v: string) => v?.slice(0, 10) || '-' },
          ]}
          size="middle"
        />
      </Card>
    </div>
  );
}
