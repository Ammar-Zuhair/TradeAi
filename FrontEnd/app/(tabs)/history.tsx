import React, { useState } from 'react';
import {
  View,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  RefreshControl,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Calendar, Filter, ChevronDown } from 'lucide-react-native';
import Animated, { FadeInDown } from 'react-native-reanimated';

import { useTheme } from '@/contexts/ThemeContext';
import Layout from '@/constants/Layout';
import { HeadingText, BodyText } from '@/components/StyledText';
import { useAccounts } from '@/contexts/AccountsContext';
import { TradeType } from '@/components/TradeCard';

// Filter options
const FILTER_OPTIONS = {
  time: ['Today', 'This Week', 'This Month', 'Last 3 Months', 'All'],
  result: ['All', 'Profit', 'Loss'],
  type: ['All', 'Buy', 'Sell'],
};

export default function HistoryScreen() {
  const { allHistory, refreshAccounts } = useAccounts();
  const { colors } = useTheme();
  const [refreshing, setRefreshing] = useState(false);
  const [timeFilter, setTimeFilter] = useState('This Month');
  const [resultFilter, setResultFilter] = useState('All');
  const [typeFilter, setTypeFilter] = useState('All');

  const [showTimeFilter, setShowTimeFilter] = useState(false);
  const [showResultFilter, setShowResultFilter] = useState(false);
  const [showTypeFilter, setShowTypeFilter] = useState(false);

  // Get real history trades
  const [filteredTrades, setFilteredTrades] = useState<TradeType[]>([]);

  const onRefresh = async () => {
    setRefreshing(true);
    await refreshAccounts();
    setRefreshing(false);
  };

  // Calculate statistics
  const totalTrades = filteredTrades.length;
  const profitableTrades = filteredTrades.filter(trade => trade.profit > 0).length;
  const winRate = totalTrades > 0 ? (profitableTrades / totalTrades) * 100 : 0;
  const totalProfit = filteredTrades.reduce((sum, trade) => sum + trade.profit, 0);

  const toggleFilter = (filterType: 'time' | 'result' | 'type') => {
    if (filterType === 'time') {
      setShowTimeFilter(!showTimeFilter);
      setShowResultFilter(false);
      setShowTypeFilter(false);
    } else if (filterType === 'result') {
      setShowResultFilter(!showResultFilter);
      setShowTimeFilter(false);
      setShowTypeFilter(false);
    } else if (filterType === 'type') {
      setShowTypeFilter(!showTypeFilter);
      setShowTimeFilter(false);
      setShowResultFilter(false);
    }
  };

  const selectFilter = (filterType: 'time' | 'result' | 'type', value: string) => {
    if (filterType === 'time') {
      setTimeFilter(value);
      setShowTimeFilter(false);
    } else if (filterType === 'result') {
      setResultFilter(value);
      setShowResultFilter(false);
    } else if (filterType === 'type') {
      setTypeFilter(value);
      setShowTypeFilter(false);
    }
  };

  // Apply filters when selection changes or trades update
  React.useEffect(() => {
    let filtered = [...allHistory];

    // Apply Time Filter
    const now = new Date();
    if (timeFilter === 'Today') {
      filtered = filtered.filter(t => {
        if (!t.closeTime) return false;
        const date = new Date(t.closeTime);
        return date.toDateString() === now.toDateString();
      });
    } else if (timeFilter === 'This Week') {
      const oneWeekAgo = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
      filtered = filtered.filter(t => t.closeTime ? new Date(t.closeTime) >= oneWeekAgo : false);
    } else if (timeFilter === 'This Month') {
      const firstDay = new Date(now.getFullYear(), now.getMonth(), 1);
      filtered = filtered.filter(t => t.closeTime ? new Date(t.closeTime) >= firstDay : false);
    } else if (timeFilter === 'Last 3 Months') {
      const threeMonthsAgo = new Date(now.getFullYear(), now.getMonth() - 3, 1);
      filtered = filtered.filter(t => t.closeTime ? new Date(t.closeTime) >= threeMonthsAgo : false);
    }

    // Apply Result Filter
    if (resultFilter === 'Profit') {
      filtered = filtered.filter(t => t.profit > 0);
    } else if (resultFilter === 'Loss') {
      filtered = filtered.filter(t => t.profit < 0);
    }

    // Apply Type Filter
    if (typeFilter !== 'All') {
      filtered = filtered.filter(t => t.direction === typeFilter.toUpperCase());
    }

    // Sort by close time descending (newest first)
    filtered.sort((a, b) => {
      const timeA = a.closeTime ? new Date(a.closeTime).getTime() : 0;
      const timeB = b.closeTime ? new Date(b.closeTime).getTime() : 0;
      return timeB - timeA;
    });

    setFilteredTrades(filtered);
  }, [timeFilter, resultFilter, typeFilter, allHistory]);

  // Dynamic styles
  const themeStyles = {
    container: { backgroundColor: colors.surface },
    title: { color: colors.text },
    card: { backgroundColor: colors.card },
    filterButton: { backgroundColor: colors.card },
    statLabel: { color: colors.placeholder },
    statValue: { color: colors.text },
    divider: { backgroundColor: colors.border },
    filterButtonText: { color: colors.placeholder },
    filterDropdown: { backgroundColor: colors.card },
    filterOptionBorder: { borderBottomColor: colors.border },
    filterOptionText: { color: colors.text },
    sectionTitle: { color: colors.text },
    noTradesText: { color: colors.placeholder },
    tableHeader: { borderBottomColor: colors.border },
    tableHeaderText: { color: colors.placeholder },
    tradeRow: { backgroundColor: colors.card },
    symbolText: { color: colors.text },
    dateText: { color: colors.placeholder },
    priceText: { color: colors.placeholder },
    closePriceText: { color: colors.text },
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
          <HeadingText style={[styles.title, themeStyles.title]}>Trade History</HeadingText>
        </View>

        <Animated.View
          style={[styles.statsContainer, themeStyles.card]}
          entering={FadeInDown.delay(200).springify()}
        >
          <View style={styles.statItem}>
            <BodyText style={[styles.statLabel, themeStyles.statLabel]}>Total Trades</BodyText>
            <HeadingText style={[styles.statValue, themeStyles.statValue]}>{totalTrades}</HeadingText>
          </View>

          <View style={[styles.statDivider, themeStyles.divider]} />

          <View style={styles.statItem}>
            <BodyText style={[styles.statLabel, themeStyles.statLabel]}>Win Rate</BodyText>
            <HeadingText style={[styles.statValue, themeStyles.statValue]}>{winRate.toFixed(1)}%</HeadingText>
          </View>

          <View style={[styles.statDivider, themeStyles.divider]} />

          <View style={styles.statItem}>
            <BodyText style={[styles.statLabel, themeStyles.statLabel]}>Total P/L</BodyText>
            <HeadingText style={[
              styles.statValue,
              { color: totalProfit >= 0 ? colors.positive : colors.negative }
            ]}>
              ${totalProfit.toFixed(2)}
            </HeadingText>
          </View>
        </Animated.View>

        <View style={styles.filtersSection}>
          <View style={styles.filterItem}>
            <TouchableOpacity
              style={[styles.filterButton, themeStyles.filterButton]}
              onPress={() => toggleFilter('time')}
            >
              <Calendar size={16} color={colors.placeholder} />
              <BodyText style={[styles.filterButtonText, themeStyles.filterButtonText]}>{timeFilter}</BodyText>
              <ChevronDown size={16} color={colors.placeholder} />
            </TouchableOpacity>

            {showTimeFilter && (
              <View style={[styles.filterDropdown, themeStyles.filterDropdown]}>
                {FILTER_OPTIONS.time.map((option, index) => (
                  <TouchableOpacity
                    key={option}
                    style={[
                      styles.filterOption,
                      index < FILTER_OPTIONS.time.length - 1 && [styles.filterOptionBorder, themeStyles.filterOptionBorder]
                    ]}
                    onPress={() => selectFilter('time', option)}
                  >
                    <BodyText style={[
                      styles.filterOptionText,
                      themeStyles.filterOptionText,
                      timeFilter === option && { color: colors.primary, fontWeight: '600', fontFamily: 'Inter-Medium' }
                    ]}>
                      {option}
                    </BodyText>
                  </TouchableOpacity>
                ))}
              </View>
            )}
          </View>

          <View style={styles.filterItem}>
            <TouchableOpacity
              style={[styles.filterButton, themeStyles.filterButton]}
              onPress={() => toggleFilter('result')}
            >
              <BodyText style={[styles.filterButtonText, themeStyles.filterButtonText]}>{resultFilter}</BodyText>
              <ChevronDown size={16} color={colors.placeholder} />
            </TouchableOpacity>

            {showResultFilter && (
              <View style={[styles.filterDropdown, themeStyles.filterDropdown]}>
                {FILTER_OPTIONS.result.map((option, index) => (
                  <TouchableOpacity
                    key={option}
                    style={[
                      styles.filterOption,
                      index < FILTER_OPTIONS.result.length - 1 && [styles.filterOptionBorder, themeStyles.filterOptionBorder]
                    ]}
                    onPress={() => selectFilter('result', option)}
                  >
                    <BodyText style={[
                      styles.filterOptionText,
                      themeStyles.filterOptionText,
                      resultFilter === option && { color: colors.primary, fontWeight: '600', fontFamily: 'Inter-Medium' }
                    ]}>
                      {option}
                    </BodyText>
                  </TouchableOpacity>
                ))}
              </View>
            )}
          </View>

          <View style={styles.filterItem}>
            <TouchableOpacity
              style={[styles.filterButton, themeStyles.filterButton]}
              onPress={() => toggleFilter('type')}
            >
              <BodyText style={[styles.filterButtonText, themeStyles.filterButtonText]}>{typeFilter}</BodyText>
              <ChevronDown size={16} color={colors.placeholder} />
            </TouchableOpacity>

            {showTypeFilter && (
              <View style={[styles.filterDropdown, themeStyles.filterDropdown]}>
                {FILTER_OPTIONS.type.map((option, index) => (
                  <TouchableOpacity
                    key={option}
                    style={[
                      styles.filterOption,
                      index < FILTER_OPTIONS.type.length - 1 && [styles.filterOptionBorder, themeStyles.filterOptionBorder]
                    ]}
                    onPress={() => selectFilter('type', option)}
                  >
                    <BodyText style={[
                      styles.filterOptionText,
                      themeStyles.filterOptionText,
                      typeFilter === option && { color: colors.primary, fontWeight: '600', fontFamily: 'Inter-Medium' }
                    ]}>
                      {option}
                    </BodyText>
                  </TouchableOpacity>
                ))}
              </View>
            )}
          </View>
        </View>

        <View style={styles.tradesSection}>
          <HeadingText style={[styles.sectionTitle, themeStyles.sectionTitle]}>Closed Trades</HeadingText>

          {filteredTrades.length === 0 ? (
            <View style={[styles.noTradesContainer, themeStyles.card]}>
              <BodyText style={[styles.noTradesText, themeStyles.noTradesText]}>
                No trade history found for the selected filters.
              </BodyText>
            </View>
          ) : (
            <>
              <View style={[styles.tableHeader, themeStyles.tableHeader]}>
                <BodyText style={[styles.tableHeaderText, themeStyles.tableHeaderText, styles.symbolCell]}>Symbol</BodyText>
                <BodyText style={[styles.tableHeaderText, themeStyles.tableHeaderText, styles.typeCell]}>Type</BodyText>
                <BodyText style={[styles.tableHeaderText, themeStyles.tableHeaderText, styles.priceCell]}>Price</BodyText>
                <BodyText style={[styles.tableHeaderText, themeStyles.tableHeaderText, styles.profitCell]}>P/L</BodyText>
              </View>

              {filteredTrades.map((trade, index) => (
                <Animated.View
                  key={trade.id}
                  entering={FadeInDown.delay(300 + (index * 70))}
                >
                  <TouchableOpacity style={[styles.tradeRow, themeStyles.tradeRow]}>
                    <View style={styles.symbolCell}>
                      <HeadingText style={[styles.symbolText, themeStyles.symbolText]}>{trade.symbol}</HeadingText>
                      <BodyText style={[styles.dateText, themeStyles.dateText]}>
                        {trade.closeTime ? new Date(trade.closeTime).toLocaleDateString() : '-'}
                      </BodyText>
                    </View>

                    <View style={styles.typeCell}>
                      <View style={[
                        styles.typeBadge,
                        {
                          backgroundColor: trade.direction === 'BUY' ?
                            'rgba(30, 185, 128, 0.15)' :
                            'rgba(255, 71, 87, 0.15)'
                        }
                      ]}>
                        <BodyText style={[
                          styles.typeText,
                          {
                            color: trade.direction === 'BUY' ?
                              colors.positive :
                              colors.negative
                          }
                        ]}>
                          {trade.direction}
                        </BodyText>
                      </View>
                    </View>

                    <View style={styles.priceCell}>
                      <BodyText style={[styles.openPriceText, themeStyles.priceText]}>
                        {trade.openPrice.toFixed(trade.symbol.includes('JPY') ? 2 : 4)}
                      </BodyText>
                      <BodyText style={[styles.closePriceText, themeStyles.closePriceText]}>
                        {trade.currentPrice.toFixed(trade.symbol.includes('JPY') ? 2 : 4)}
                      </BodyText>
                    </View>

                    <View style={styles.profitCell}>
                      <BodyText style={[
                        styles.profitText,
                        {
                          color: trade.profit >= 0 ?
                            colors.positive :
                            colors.negative
                        }
                      ]}>
                        {trade.profit >= 0 ? '+' : ''}{trade.profit.toFixed(2)}
                      </BodyText>
                    </View>
                  </TouchableOpacity>
                </Animated.View>
              ))}
            </>
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
    height: 36,
    borderRadius: Layout.borderRadius.md,
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: Layout.spacing.md,
  },
  statsContainer: {
    flexDirection: 'row',
    borderRadius: Layout.borderRadius.lg,
    padding: Layout.spacing.lg,
    marginBottom: Layout.spacing.lg,
    justifyContent: 'space-between',
  },
  statItem: {
    alignItems: 'center',
  },
  statLabel: {
    fontSize: 12,
    marginBottom: 4,
  },
  statValue: {
    fontSize: 18,
    fontWeight: '600',
    fontFamily: 'Inter-Medium',
  },
  statDivider: {
    width: 1,
  },
  filtersSection: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: Layout.spacing.lg,
  },
  filterItem: {
    position: 'relative',
  },
  filterButtonText: {
    fontSize: 14,
    marginHorizontal: Layout.spacing.xs,
  },
  filterDropdown: {
    position: 'absolute',
    top: 40,
    left: 0,
    right: 0,
    borderRadius: Layout.borderRadius.md,
    padding: Layout.spacing.xs,
    zIndex: 10,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 4,
    elevation: 8,
  },
  filterOption: {
    paddingVertical: Layout.spacing.sm,
    paddingHorizontal: Layout.spacing.md,
  },
  filterOptionBorder: {
    borderBottomWidth: 1,
  },
  filterOptionText: {
    fontSize: 14,
  },
  tradesSection: {
    marginBottom: Layout.spacing.xxl,
  },
  sectionTitle: {
    fontSize: 18,
    marginBottom: Layout.spacing.md,
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
  tableHeader: {
    flexDirection: 'row',
    paddingVertical: Layout.spacing.sm,
    borderBottomWidth: 1,
    marginBottom: Layout.spacing.sm,
  },
  tableHeaderText: {
    fontSize: 12,
    fontWeight: '500',
    fontFamily: 'Inter-Medium',
  },
  tradeRow: {
    flexDirection: 'row',
    padding: Layout.spacing.md,
    borderRadius: Layout.borderRadius.md,
    marginBottom: Layout.spacing.sm,
  },
  symbolCell: {
    flex: 3,
  },
  symbolText: {
    fontSize: 16,
    marginBottom: 2,
  },
  dateText: {
    fontSize: 12,
  },
  typeCell: {
    flex: 2,
    justifyContent: 'center',
  },
  typeBadge: {
    paddingHorizontal: Layout.spacing.sm,
    paddingVertical: Layout.spacing.xs,
    borderRadius: Layout.borderRadius.sm,
    alignSelf: 'flex-start',
  },
  typeText: {
    fontSize: 12,
    fontWeight: '500',
    fontFamily: 'Inter-Medium',
  },
  priceCell: {
    flex: 2,
    justifyContent: 'center',
  },
  openPriceText: {
    fontSize: 12,
    marginBottom: 2,
  },
  closePriceText: {
    fontSize: 12,
  },
  profitCell: {
    flex: 2,
    justifyContent: 'center',
    alignItems: 'flex-end',
  },
  profitText: {
    fontSize: 16,
    fontWeight: '600',
    fontFamily: 'Inter-Medium',
  },
});