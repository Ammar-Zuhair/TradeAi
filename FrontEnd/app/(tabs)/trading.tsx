import React, { useState } from 'react';
import {
  View,
  StyleSheet,
  ScrollView,
  RefreshControl,
  TouchableOpacity,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { TrendingUp, TrendingDown, Calendar, Filter } from 'lucide-react-native';
import Animated, { FadeInDown } from 'react-native-reanimated';

import { useAccounts } from '@/contexts/AccountsContext';
import { useTheme } from '@/contexts/ThemeContext';
import Layout from '@/constants/Layout';
import { HeadingText, BodyText } from '@/components/StyledText';
import TradeCard, { TradeType } from '@/components/TradeCard';

export default function TradingScreen() {
  const { accounts, getAccountTrades, activeAccountId } = useAccounts();
  const { colors } = useTheme();
  const [refreshing, setRefreshing] = useState(false);
  const [activeFilter, setActiveFilter] = useState('all');

  // Get all trades from all accounts (or filtered by active account)
  const allTrades = accounts.reduce<TradeType[]>((acc, account) => {
    // If activeAccountId is set, only include that account
    if (activeFilter !== 'all' && activeAccountId && account.id !== activeAccountId) return acc;
    // Wait, activeFilter is for buy/sell. I need to check activeAccountId from context.
    if (activeAccountId && account.id !== activeAccountId) return acc;

    const accountTrades = getAccountTrades(account.id);
    return [...acc, ...accountTrades];
  }, []);

  // Filter trades based on activeFilter
  const filteredTrades = allTrades.filter(trade => {
    if (activeFilter === 'buy') {
      return trade.direction === 'BUY';
    } else if (activeFilter === 'sell') {
      return trade.direction === 'SELL';
    }
    return true;
  });

  // Calculate totals
  const totalProfit = allTrades.reduce((sum, trade) => sum + trade.profit, 0);
  const totalBuyProfit = allTrades
    .filter(trade => trade.direction === 'BUY')
    .reduce((sum, trade) => sum + trade.profit, 0);
  const totalSellProfit = allTrades
    .filter(trade => trade.direction === 'SELL')
    .reduce((sum, trade) => sum + trade.profit, 0);

  const onRefresh = async () => {
    setRefreshing(true);

    // Simulate API refresh
    await new Promise(resolve => setTimeout(resolve, 1500));

    setRefreshing(false);
  };

  const handleTradePress = (id: string) => {
    // Navigate to trade details or implement action
    console.log('Trade pressed:', id);
  };

  // Dynamic styles
  const themeStyles = {
    container: { backgroundColor: colors.surface },
    title: { color: colors.text },
    card: { backgroundColor: colors.card },
    filterButton: { backgroundColor: colors.card },
    statLabel: { color: colors.placeholder },
    filterContainer: { backgroundColor: colors.card },
    filterText: { color: colors.placeholder },
    activeFilterText: { color: '#fff' }, // Keep white for active state on primary color
    dateRangeText: { color: colors.placeholder },
    noTradesText: { color: colors.placeholder },
  };

  return (
    <SafeAreaView style={[styles.container, themeStyles.container]} edges={['top']}>
      <ScrollView
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
        refreshControl={
          <RefreshControl
            refreshing={refreshing}
            onRefresh={onRefresh}
            tintColor={colors.primary}
            colors={[colors.primary]}
          />
        }
      >
        <View style={styles.header}>
          <HeadingText style={[styles.title, themeStyles.title]}>Open Trades</HeadingText>
        </View>

        <Animated.View
          style={styles.statsContainer}
          entering={FadeInDown.delay(200).springify()}
        >
          <View style={[styles.statCard, themeStyles.card]}>
            <View style={styles.statIconContainer}>
              <TrendingUp
                size={20}
                color={totalProfit >= 0 ? colors.positive : colors.negative}
              />
            </View>
            <BodyText style={[styles.statLabel, themeStyles.statLabel]}>Total P/L</BodyText>
            <HeadingText style={[
              styles.statValue,
              { color: totalProfit >= 0 ? colors.positive : colors.negative }
            ]}>
              ${totalProfit.toFixed(2)}
            </HeadingText>
          </View>

          <View style={[styles.statCard, themeStyles.card]}>
            <View style={[styles.statIconContainer, styles.buyIcon]}>
              <TrendingUp size={20} color={colors.positive} />
            </View>
            <BodyText style={[styles.statLabel, themeStyles.statLabel]}>Buy Positions</BodyText>
            <HeadingText style={[
              styles.statValue,
              { color: totalBuyProfit >= 0 ? colors.positive : colors.negative }
            ]}>
              ${totalBuyProfit.toFixed(2)}
            </HeadingText>
          </View>

          <View style={[styles.statCard, themeStyles.card]}>
            <View style={[styles.statIconContainer, styles.sellIcon]}>
              <TrendingDown size={20} color={colors.negative} />
            </View>
            <BodyText style={[styles.statLabel, themeStyles.statLabel]}>Sell Positions</BodyText>
            <HeadingText style={[
              styles.statValue,
              { color: totalSellProfit >= 0 ? colors.positive : colors.negative }
            ]}>
              ${totalSellProfit.toFixed(2)}
            </HeadingText>
          </View>
        </Animated.View>

        <View style={[styles.filterContainer, themeStyles.filterContainer]}>
          <TouchableOpacity
            style={[
              styles.filterTab,
              activeFilter === 'all' && { backgroundColor: colors.primary }
            ]}
            onPress={() => setActiveFilter('all')}
          >
            <BodyText style={[
              styles.filterText,
              themeStyles.filterText,
              activeFilter === 'all' && themeStyles.activeFilterText
            ]}>
              All
            </BodyText>
          </TouchableOpacity>

          <TouchableOpacity
            style={[
              styles.filterTab,
              activeFilter === 'buy' && { backgroundColor: colors.primary }
            ]}
            onPress={() => setActiveFilter('buy')}
          >
            <BodyText style={[
              styles.filterText,
              themeStyles.filterText,
              activeFilter === 'buy' && themeStyles.activeFilterText
            ]}>
              Buy
            </BodyText>
          </TouchableOpacity>

          <TouchableOpacity
            style={[
              styles.filterTab,
              activeFilter === 'sell' && { backgroundColor: colors.primary }
            ]}
            onPress={() => setActiveFilter('sell')}
          >
            <BodyText style={[
              styles.filterText,
              themeStyles.filterText,
              activeFilter === 'sell' && themeStyles.activeFilterText
            ]}>
              Sell
            </BodyText>
          </TouchableOpacity>
        </View>

        <View style={styles.dateRangeContainer}>
          <Calendar size={16} color={colors.placeholder} />
          <BodyText style={[styles.dateRangeText, themeStyles.dateRangeText]}>Today's Trades</BodyText>
        </View>

        <View style={styles.tradesContainer}>
          {filteredTrades.length === 0 ? (
            <View style={[styles.noTradesContainer, themeStyles.card]}>
              <BodyText style={[styles.noTradesText, themeStyles.noTradesText]}>
                No open trades found. Start trading to see your positions here.
              </BodyText>
            </View>
          ) : (
            filteredTrades.map((trade, index) => (
              <Animated.View
                key={trade.id}
                entering={FadeInDown.delay(300 + (index * 100)).springify()}
              >
                <TradeCard trade={trade} onPress={handleTradePress} />
              </Animated.View>
            ))
          )}
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  scrollContent: {
    padding: Layout.spacing.md,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: Layout.spacing.lg,
  },
  title: {
    fontSize: 24,
  },
  filterButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    justifyContent: 'center',
    alignItems: 'center',
  },
  statsContainer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: Layout.spacing.lg,
  },
  statCard: {
    flex: 1,
    borderRadius: Layout.borderRadius.md,
    padding: Layout.spacing.md,
    marginHorizontal: 4,
    alignItems: 'center',
  },
  statIconContainer: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: 'rgba(30, 185, 128, 0.15)',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 8,
  },
  buyIcon: {
    backgroundColor: 'rgba(30, 185, 128, 0.15)',
  },
  sellIcon: {
    backgroundColor: 'rgba(255, 71, 87, 0.15)',
  },
  statLabel: {
    fontSize: 12,
    marginBottom: 4,
  },
  statValue: {
    fontSize: 16,
    fontWeight: '600',
    fontFamily: 'Inter-Medium',
  },
  filterContainer: {
    flexDirection: 'row',
    borderRadius: Layout.borderRadius.md,
    marginBottom: Layout.spacing.md,
    padding: 2, // Reduced from 4
  },
  filterTab: {
    flex: 1,
    paddingVertical: 12, // Increased from Layout.spacing.sm (usually 8)
    alignItems: 'center',
    borderRadius: Layout.borderRadius.sm,
  },
  filterText: {
    fontSize: 14,
    fontFamily: 'Inter-Medium',
  },
  dateRangeContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: Layout.spacing.md,
  },
  dateRangeText: {
    fontSize: 14,
    marginLeft: Layout.spacing.sm,
  },
  tradesContainer: {
    marginBottom: Layout.spacing.xl,
  },
  noTradesContainer: {
    borderRadius: Layout.borderRadius.lg,
    padding: Layout.spacing.lg,
    alignItems: 'center',
    justifyContent: 'center',
    height: 150,
  },
  noTradesText: {
    textAlign: 'center',
  },
});