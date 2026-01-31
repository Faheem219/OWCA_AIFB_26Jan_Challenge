/**
 * Order Service for managing buyer/vendor orders
 */

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

export interface Order {
  id: string;
  product_id: string;
  product_name: string;
  product_image?: string;
  buyer_id?: string;
  buyer_name?: string;
  buyer_email?: string;
  vendor_id: string;
  vendor_name: string;
  quantity: number;
  unit: string;
  original_price: number;
  offered_price: number;
  total_amount: number;
  message?: string;
  status: 'pending' | 'confirmed' | 'shipped' | 'delivered' | 'cancelled';
  tracking_number?: string;
  estimated_delivery?: string;
  created_at: string;
  updated_at: string;
}

export interface CreateOrderData {
  product_id: string;
  vendor_id: string;
  quantity: number;
  offered_price: number;
  message?: string;
}

export interface OrdersResponse {
  orders: Order[];
  total: number;
  has_more: boolean;
}

class OrderService {
  private getHeaders(): HeadersInit {
    const token = localStorage.getItem('accessToken');
    return {
      'Content-Type': 'application/json',
      ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
    };
  }

  async createOrder(data: CreateOrderData): Promise<Order> {
    const response = await fetch(`${API_BASE_URL}/orders/`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to create order');
    }

    const result = await response.json();
    return result.order;
  }

  async getBuyerOrders(status?: string): Promise<OrdersResponse> {
    const params = new URLSearchParams();
    if (status) params.append('status', status);

    const response = await fetch(`${API_BASE_URL}/orders/buyer?${params.toString()}`, {
      method: 'GET',
      headers: this.getHeaders(),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to fetch orders');
    }

    return response.json();
  }

  async getVendorOrders(status?: string): Promise<OrdersResponse> {
    const params = new URLSearchParams();
    if (status) params.append('status', status);

    const response = await fetch(`${API_BASE_URL}/orders/vendor?${params.toString()}`, {
      method: 'GET',
      headers: this.getHeaders(),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to fetch orders');
    }

    return response.json();
  }

  async getOrder(orderId: string): Promise<Order> {
    const response = await fetch(`${API_BASE_URL}/orders/${orderId}`, {
      method: 'GET',
      headers: this.getHeaders(),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to fetch order');
    }

    return response.json();
  }

  async updateOrderStatus(orderId: string, status: string, trackingInfo?: {
    tracking_number?: string;
    estimated_delivery?: string;
  }): Promise<Order> {
    const response = await fetch(`${API_BASE_URL}/orders/${orderId}/status`, {
      method: 'PATCH',
      headers: this.getHeaders(),
      body: JSON.stringify({
        status,
        ...trackingInfo,
      }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to update order status');
    }

    return response.json();
  }

  async cancelOrder(orderId: string): Promise<Order> {
    return this.updateOrderStatus(orderId, 'cancelled');
  }

  async confirmOrder(orderId: string): Promise<Order> {
    return this.updateOrderStatus(orderId, 'confirmed');
  }

  async shipOrder(orderId: string, trackingNumber?: string, estimatedDelivery?: string): Promise<Order> {
    return this.updateOrderStatus(orderId, 'shipped', {
      tracking_number: trackingNumber,
      estimated_delivery: estimatedDelivery,
    });
  }

  async markDelivered(orderId: string): Promise<Order> {
    return this.updateOrderStatus(orderId, 'delivered');
  }
}

export const orderService = new OrderService();
export default orderService;
