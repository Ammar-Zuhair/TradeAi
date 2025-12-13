import React, { createContext, useState, useContext, useEffect } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { AccountType } from '@/components/AccountCard';
import { TradeType } from '@/components/TradeCard';
import { accountService, tradeService } from '@/services/api';
import { useAuth } from './AuthContext';
import { DBAccount, DBTrade } from '@/types/schema';
import { getTradeTypeLabel, getTradeStatusLabel, getAccountTypeLabel } from '@/utils/formatting';

type AccountsContextType = {
  accounts: AccountType[];
  isLoading: boolean;
  error: string | null;
  addAccount: (accountData: {
    accountName: string;
    loginNumber: string;
    password: string;
    server: string;
    serverId?: number;
    riskPercentage: number;
    strategy?: 'All' | 'FVG + Trend' | 'Voting';
  }) => Promise<{ success: boolean; message: string; mt5Info?: any }>;
  removeAccount: (id: string) => Promise<void>;
  refreshAccounts: () => Promise<void>;
  getAccountTrades: (accountId: string) => TradeType[];
  getAccountHistory: (accountId: string) => TradeType[];
  allHistory: TradeType[];
  activeAccountId: string | null;
  setActiveAccount: (id: string | null) => void;
  closeTrade: (ticket: number) => Promise<{ success: boolean; message: string }>;
  clearError: () => void;
};

const AccountsContext = createContext<AccountsContextType>({
  accounts: [],
  isLoading: false,
  error: null,
  addAccount: async () => ({ success: false, message: '' }),
  removeAccount: async () => { },
  refreshAccounts: async () => { },
  getAccountTrades: () => [],
  getAccountHistory: () => [],
  allHistory: [],
  activeAccountId: null,
  setActiveAccount: () => { },
  closeTrade: async () => ({ success: false, message: 'Not initialized' }),
  clearError: () => { },
});

export const useAccounts = () => useContext(AccountsContext);

export const AccountsProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { user } = useAuth();
  const [accounts, setAccounts] = useState<AccountType[]>([]);
  const [trades, setTrades] = useState<Record<string, TradeType[]>>({});
  const [history, setHistory] = useState<Record<string, TradeType[]>>({});
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeAccountId, setActiveAccount] = useState<string | null>(null);

  // Load accounts from API when user logs in
  useEffect(() => {
    if (user && user.token) {
      refreshAccounts();

      // Poll for updates every 2 seconds
      const interval = setInterval(() => {
        refreshAccounts(true); // silent refresh
      }, 2000);

      return () => clearInterval(interval);
    }
  }, [user]);

  const refreshAccounts = async (silent = false) => {
    if (!user || !user.token) return;

    if (!silent) setIsLoading(true);
    // Don't clear error on silent refresh to avoid flickering
    if (!silent) setError(null);

    try {
      // Backend now determines user from token, no need to pass ID
      const response = await accountService.getAccounts(user.token);

      // Transform API response to AccountType format
      const transformedAccounts: AccountType[] = response.map((acc: DBAccount) => ({
        id: acc.AccountID.toString(),
        name: acc.AccountName || `Account ${acc.AccountLoginNumber}`, // Use AccountName if available
        balance: parseFloat(acc.AccountBalance),
        currency: 'USD',
        profit: 0, // Will be updated below
        openTrades: 0, // Will be updated below
        server: acc.ServerName || acc.ServerID.toString(), // ✅ Use ServerName from backend
        type: getAccountTypeLabel(acc.AccountType),
        riskPercentage: parseFloat(acc.RiskPercentage),
        strategy: acc.TradingStrategy,
      }));

      // Fetch trades for each account
      const newTrades: Record<string, TradeType[]> = {};
      const newHistory: Record<string, TradeType[]> = {};

      for (const acc of transformedAccounts) {
        try {
          const tradeResponse = await tradeService.getTrades(user.token, parseInt(acc.id));

          const accTrades: TradeType[] = tradeResponse.map((t: DBTrade) => ({
            id: t.TradeID.toString(),
            symbol: t.AccountSymbol || t.PairName || t.TradeAsset || `Pair:${t.MappingID}`, // ✅ Use AccountSymbol
            direction: getTradeTypeLabel(t.TradeType),
            openPrice: parseFloat(t.TradeOpenPrice),
            currentPrice: parseFloat(t.TradeClosePrice || t.TradeOpenPrice), // TradeClosePrice contains current price for open trades
            profit: t.TradeProfitLose ? parseFloat(t.TradeProfitLose) : 0.0,
            openTime: t.TradeOpenTime,
            closeTime: t.TradeCloseTime, // Add closeTime
            status: getTradeStatusLabel(t.TradeStatus), // 1=Open, 2=Winning, 3=Losing
            ticket: t.TradeID, // TradeID IS the ticket number
            stopLoss: t.TradeSL ? parseFloat(t.TradeSL) : undefined,
            takeProfit: t.TradeTP ? parseFloat(t.TradeTP) : undefined,
            lotSize: t.TradeLotsize ? parseFloat(t.TradeLotsize) : undefined,
          }));

          // Filter only OPEN trades for the context state (history will fetch closed)
          newTrades[acc.id] = accTrades.filter(t => t.status === 'OPEN');
          newHistory[acc.id] = accTrades.filter(t => t.status !== 'OPEN');

          // Update Account Stats
          const openTradesCount = newTrades[acc.id].length;
          const currentProfit = newTrades[acc.id].reduce((sum, t) => sum + t.profit, 0);

          acc.openTrades = openTradesCount;
          acc.profit = currentProfit;

        } catch (err) {
          console.log(`Failed to fetch trades for account ${acc.id}`, err);
          newTrades[acc.id] = [];
          newHistory[acc.id] = [];
        }
      }

      setAccounts(transformedAccounts);
      setTrades(newTrades);
      setHistory(newHistory);

    } catch (e: any) {
      console.error('Failed to load accounts', e);
      if (!silent) setError(e.response?.data?.detail || 'Failed to load accounts');
    } finally {
      if (!silent) setIsLoading(false);
    }
  };

  const addAccount = async (accountData: {
    accountName: string;
    loginNumber: string;
    password: string;
    server: string;
    serverId?: number;
    riskPercentage: number;
    strategy?: 'All' | 'FVG + Trend' | 'Voting';
  }): Promise<{ success: boolean; message: string; mt5Info?: any }> => {
    if (!user || !user.token) {
      return { success: false, message: 'User not authenticated' };
    }

    setIsLoading(true);
    setError(null);

    try {
      const userId = parseInt(user.id); // Convert string id to number
      const response = await accountService.createAccount(user.token, {
        UserID: userId,
        AccountName: accountData.accountName,
        AccountLoginNumber: parseInt(accountData.loginNumber),
        AccountLoginPassword: accountData.password,
        // AccountLoginServer removed. ServerID is sufficient.
        ServerID: accountData.serverId,
        RiskPercentage: accountData.riskPercentage,
        TradingStrategy: accountData.strategy || 'All',
      });

      if (response.success) {
        // Refresh accounts list
        await refreshAccounts();

        return {
          success: true,
          message: response.message,
          mt5Info: response.mt5_info,
        };
      } else {
        setError(response.message);
        return {
          success: false,
          message: response.message,
          mt5Info: null,
        };
      }
    } catch (e: any) {
      const errorMsg = e.response?.data?.detail || 'Failed to add account';
      setError(errorMsg);
      return {
        success: false,
        message: errorMsg,
        mt5Info: null,
      };
    } finally {
      setIsLoading(false);
    }
  };

  const removeAccount = async (id: string) => {
    if (!user || !user.token) return;

    setIsLoading(true);
    setError(null);

    try {
      await accountService.deleteAccount(user.token, parseInt(id));
      await refreshAccounts();
    } catch (e: any) {
      console.error('Error removing account', e);
      setError(e.response?.data?.detail || 'Failed to remove account');
    } finally {
      setIsLoading(false);
    }
  };

  const getAccountTrades = (accountId: string): TradeType[] => {
    return trades[accountId] || [];
  };

  const getAccountHistory = (accountId: string): TradeType[] => {
    return history[accountId] || [];
  };

  const allHistory = React.useMemo(() => Object.values(history).flat(), [history]);

  const closeTrade = async (ticket: number): Promise<{ success: boolean; message: string }> => {
    if (!user || !user.token) {
      return { success: false, message: 'User not authenticated' };
    }

    try {
      const response = await tradeService.closeTrade(user.token, ticket);
      await refreshAccounts();
      return { success: true, message: response.message || 'Trade closed successfully' };
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || 'Failed to close trade';
      setError(errorMessage);
      return { success: false, message: errorMessage };
    }
  };

  const clearError = () => {
    setError(null);
  };

  return (
    <AccountsContext.Provider
      value={{
        accounts,
        isLoading,
        error,
        addAccount,
        removeAccount,
        refreshAccounts,
        getAccountTrades,
        getAccountHistory,
        allHistory,
        activeAccountId,
        setActiveAccount,
        closeTrade,
        clearError,
      }}
    >
      {children}
    </AccountsContext.Provider>
  );
};