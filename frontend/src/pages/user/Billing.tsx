
import { useEffect, useState } from 'react';
import { Card, Table, Button, Modal, InputNumber, message, Statistic, Row, Col } from 'antd';
import { DollarOutlined } from '@ant-design/icons';
import { useTranslation } from 'react-i18next';
import { useAuthStore } from '../../stores/authStore';
import apiClient from '../../api/client';

export default function Billing() {
  const { t } = useTranslation();
  const { user, updateBalance } = useAuthStore();
  const [consumption, setConsumption] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [rechargeOpen, setRechargeOpen] = useState(false);
  const [amount, setAmount] = useState(1000);

  const fetchConsumption = async () => {
    try {
      const res = await apiClient.get('/billing/consumption');
      setConsumption(res.data.data.items);
    } catch {}
  };

  useEffect(() => { fetchConsumption(); }, []);

  const handleRecharge = async () => {
    try {
      const res = await apiClient.post('/billing/recharge', { amount_points: amount, amount_money: amount / 100 });
      const orderId = res.data.data.order_id;
      await apiClient.post(`/billing/recharge/${orderId}/confirm`);
      const profileRes = await apiClient.get('/user/profile');
      updateBalance(profileRes.data.data.balance);
      message.success(t('billing.rechargeSuccess'));
      setRechargeOpen(false);
    } catch {
      message.error(t('billing.rechargeFailed'));
    }
  };

  return (
    <div>
      <h2 className="page-header">{t('nav.billing')}</h2>
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12}>
          <Card>
            <Statistic title={t('billing.balance')} value={user?.balance || 0} prefix={<DollarOutlined />} />
            <Button type="primary" style={{ marginTop: 16 }} onClick={() => setRechargeOpen(true)}>
              {t('billing.recharge')}
            </Button>
          </Card>
        </Col>
      </Row>

      <Card title={t('billing.consumptionHistory')}>
        <Table
          dataSource={consumption}
          rowKey="id"
          columns={[
            { title: t('billing.points'), dataIndex: 'points', key: 'points' },
            { title: t('billing.description'), dataIndex: 'description', key: 'description' },
            { title: t('billing.time'), dataIndex: 'created_at', key: 'created_at', render: (v: string) => v?.slice(0, 16) || '-' },
          ]}
          size="middle"
        />
      </Card>

      <Modal title={t('billing.recharge')} open={rechargeOpen} onOk={handleRecharge} onCancel={() => setRechargeOpen(false)}>
        <InputNumber
          style={{ width: '100%' }}
          min={100}
          max={100000}
          step={100}
          value={amount}
          onChange={(v) => setAmount(v || 100)}
          addonAfter={t('billing.points')}
        />
        <p style={{ marginTop: 8, color: '#666' }}>{t('billing.amount')}: ¥{(amount / 100).toFixed(2)}</p>
      </Modal>
    </div>
  );
}
