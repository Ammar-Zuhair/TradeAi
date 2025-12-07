import React, { useState } from 'react';
import { Modal, View, Text, TouchableOpacity, StyleSheet, ScrollView } from 'react-native';
import { X, ChevronLeft } from 'lucide-react-native';
import Layout from '@/constants/Layout';
import { useTheme } from '@/contexts/ThemeContext';

interface DatePickerModalProps {
    visible: boolean;
    onClose: () => void;
    onSelect: (date: string) => void;
    initialDate?: string;
}

export default function DatePickerModal({ visible, onClose, onSelect, initialDate }: DatePickerModalProps) {
    const { colors } = useTheme();
    const [step, setStep] = useState<'year' | 'month' | 'day'>('year');
    const [selectedYear, setSelectedYear] = useState<number>(new Date().getFullYear());
    const [selectedMonth, setSelectedMonth] = useState<number>(0);

    const currentYear = new Date().getFullYear();
    const years = Array.from({ length: 100 }, (_, i) => currentYear - i);
    const months = [
        'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
        'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'
    ];

    const getDaysInMonth = (year: number, month: number) => {
        return new Date(year, month + 1, 0).getDate();
    };

    const handleYearSelect = (year: number) => {
        setSelectedYear(year);
        setStep('month');
    };

    const handleMonthSelect = (monthIndex: number) => {
        setSelectedMonth(monthIndex);
        setStep('day');
    };

    const handleDaySelect = (day: number) => {
        const formattedDate = `${selectedYear}-${String(selectedMonth + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
        onSelect(formattedDate);
        resetAndClose();
    };

    const resetAndClose = () => {
        setStep('year');
        onClose();
    };

    const handleBack = () => {
        if (step === 'day') setStep('month');
        else if (step === 'month') setStep('year');
    };

    return (
        <Modal visible={visible} transparent animationType="fade" onRequestClose={resetAndClose}>
            <View style={styles.overlay}>
                <View style={[styles.content, { backgroundColor: colors.surface }]}>
                    <View style={styles.header}>
                        <View style={{ width: 32 }}>
                            {step !== 'year' && (
                                <TouchableOpacity onPress={handleBack} style={styles.iconButton}>
                                    <ChevronLeft size={24} color={colors.text} />
                                </TouchableOpacity>
                            )}
                        </View>
                        <Text style={[styles.title, { color: colors.text }]}>
                            {step === 'year' ? 'Select Year' : step === 'month' ? 'Select Month' : 'Select Day'}
                        </Text>
                        <TouchableOpacity onPress={resetAndClose} style={styles.iconButton}>
                            <X size={24} color={colors.text} />
                        </TouchableOpacity>
                    </View>

                    <ScrollView contentContainerStyle={styles.grid} showsVerticalScrollIndicator={false}>
                        {step === 'year' && years.map(year => (
                            <TouchableOpacity
                                key={year}
                                style={[styles.item, { borderColor: colors.border, backgroundColor: colors.card }]}
                                onPress={() => handleYearSelect(year)}
                            >
                                <Text style={[styles.itemText, { color: colors.text }]}>{year}</Text>
                            </TouchableOpacity>
                        ))}

                        {step === 'month' && months.map((month, index) => (
                            <TouchableOpacity
                                key={month}
                                style={[styles.item, { borderColor: colors.border, backgroundColor: colors.card }]}
                                onPress={() => handleMonthSelect(index)}
                            >
                                <Text style={[styles.itemText, { color: colors.text }]}>{month}</Text>
                            </TouchableOpacity>
                        ))}

                        {step === 'day' && Array.from({ length: getDaysInMonth(selectedYear, selectedMonth) }, (_, i) => i + 1).map(day => (
                            <TouchableOpacity
                                key={day}
                                style={[styles.item, { borderColor: colors.border, backgroundColor: colors.card, width: '22%' }]}
                                onPress={() => handleDaySelect(day)}
                            >
                                <Text style={[styles.itemText, { color: colors.text }]}>{day}</Text>
                            </TouchableOpacity>
                        ))}
                    </ScrollView>
                </View>
            </View>
        </Modal>
    );
}

const styles = StyleSheet.create({
    overlay: {
        flex: 1,
        backgroundColor: 'rgba(0,0,0,0.5)',
        justifyContent: 'center',
        padding: Layout.spacing.lg,
    },
    content: {
        borderRadius: Layout.borderRadius.lg,
        maxHeight: '60%',
        padding: Layout.spacing.md,
        elevation: 5,
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 2 },
        shadowOpacity: 0.25,
        shadowRadius: 3.84,
    },
    header: {
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'space-between',
        marginBottom: Layout.spacing.md,
    },
    title: {
        fontSize: 18,
        fontWeight: 'bold',
        textAlign: 'center',
    },
    iconButton: {
        padding: 4,
    },
    grid: {
        flexDirection: 'row',
        flexWrap: 'wrap',
        justifyContent: 'center',
        gap: Layout.spacing.sm,
        paddingBottom: Layout.spacing.md,
    },
    item: {
        width: '30%',
        paddingVertical: Layout.spacing.md,
        justifyContent: 'center',
        alignItems: 'center',
        borderWidth: 1,
        borderRadius: Layout.borderRadius.md,
        marginBottom: Layout.spacing.xs,
    },
    itemText: {
        fontSize: 16,
        fontWeight: '500',
    },
});
