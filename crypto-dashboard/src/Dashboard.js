import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Container, Row, Col, Card, ListGroup, Table, Button } from 'react-bootstrap';
import { Line } from 'react-chartjs-2';
import { Chart as ChartJS } from 'chart.js/auto';

const Dashboard = () => {
  const [priceData, setPriceData] = useState(null);
  const [saldo, setSaldo] = useState(null);
  const [transactions, setTransactions] = useState([]);
  const [indicators, setIndicators] = useState({});
  const [historicalPrices, setHistoricalPrices] = useState([]);
  const [error, setError] = useState(null);

  useEffect(() => {
    // Fetch saldo
    axios.get('http://localhost:5000/api/saldo')
      .then(response => {
        setSaldo(response.data);
      })
      .catch(error => {
        console.error('Error fetching saldo:', error);
      });

    // Fetch predicted price
    axios.get('http://localhost:5000/api/predict_price')
      .then(response => {
        setPriceData(response.data);
      })
      .catch(error => {
        console.error('Error fetching price data:', error);
      });

    // Fetch technical indicators
    axios.get('http://localhost:5000/api/technical_indicators')
      .then(response => {
        setIndicators(response.data);
      })
      .catch(error => {
        console.error('Error fetching indicators:', error);
      });

    // Fetch historical prices
    axios.get('http://localhost:5000/api/historical_prices')
      .then(response => {
        if (response.data.error) {
          setError(response.data.error);
        } else {
          setHistoricalPrices(response.data);
        }
      })
      .catch(error => {
        setError('Gagal mengambil data historis.');
        console.error('Error fetching historical prices:', error);
      });

    // Fetch transaction history
    axios.get('http://localhost:5000/api/transaction_history')
      .then(response => {
        setTransactions(response.data);
      })
      .catch(error => {
        console.error('Error fetching transaction history:', error);
      });
  }, []);

  if (error) {
    return <div>{error}</div>;
  }

  if (!priceData || !saldo || transactions.length === 0 || !indicators) {
    return <div>Loading...</div>;
  }

  // Chart Data
  const chartData = {
    labels: historicalPrices.length > 0 ? historicalPrices.map(item => item.date) : ['No Data'],
    datasets: [
      {
        label: 'Price History',
        data: historicalPrices.length > 0 ? historicalPrices.map(item => item.price) : [0],
        borderColor: 'rgba(75,192,192,1)',
        backgroundColor: 'rgba(75,192,192,0.2)',
        fill: true,
      },
    ],
  };

  return (
    <Container fluid>
      <Row>
        <Col md={4}>
          <Card>
            <Card.Header>Saldo Anda</Card.Header>
            <Card.Body>
              <ListGroup variant="flush">
                <ListGroup.Item>Saldo IDR: {saldo.idr} IDR</ListGroup.Item>
                <ListGroup.Item>Saldo BTC: {saldo.btc} BTC</ListGroup.Item>
              </ListGroup>
            </Card.Body>
          </Card>
        </Col>

        <Col md={8}>
          <Card>
            <Card.Header>Prediksi Harga dan Indikator Teknikal</Card.Header>
            <Card.Body>
              <Row>
                <Col md={6}>
                  <p>Current Price: {priceData.current_price} IDR</p>
                  <p>Predicted Price: {priceData.predicted_price} IDR</p>
                </Col>
                <Col md={6}>
                  <p>RSI: {indicators.RSI}</p>
                  <p>SMA: {indicators.SMA}</p>
                  <p>BB Upper: {indicators.BB_Upper}</p>
                  <p>BB Lower: {indicators.BB_Lower}</p>
                </Col>
              </Row>

              {historicalPrices.length > 0 ? (
                <Line data={chartData} />
              ) : (
                <p>Tidak ada data historis untuk ditampilkan.</p>
              )}
            </Card.Body>
          </Card>
        </Col>
      </Row>

      <Row>
        <Col md={12}>
          <Card>
            <Card.Header>Riwayat Transaksi</Card.Header>
            <Card.Body>
              <Table striped bordered hover responsive>
                <thead>
                  <tr>
                    <th>Timestamp</th>
                    <th>Action</th>
                    <th>Price</th>
                    <th>Jumlah Crypto</th>
                  </tr>
                </thead>
                <tbody>
                  {transactions.length > 0 ? (
                    transactions.map((transaction, index) => (
                      <tr key={index}>
                        <td>{new Date(transaction.timestamp).toLocaleString()}</td>
                        <td>{transaction.action}</td>
                        <td>{transaction.price} IDR</td>
                        <td>{transaction.jumlah_crypto}</td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan="4" className="text-center">Tidak ada riwayat transaksi.</td>
                    </tr>
                  )}
                </tbody>
              </Table>
            </Card.Body>
          </Card>
        </Col>
      </Row>
    </Container>
  );
};

export default Dashboard;
