#pragma once

namespace qrawlr
{
    template <typename T>
    class Flags
    {
    public:
        Flags();
        ~Flags();
    public:
        void set(T flag);
        void unset(T flag);
        bool is_set(T flag) const;
    private:
        unsigned long long m_flags;
    };

    template <typename T>
    Flags<T>::Flags()
        : m_flags(0)
    {}
    
    template <typename T>
    Flags<T>::~Flags()
    {}

    template <typename T>
    void Flags<T>::set(T flag)
    {
        m_flags |= 1 << static_cast<unsigned long long>(flag);
    }

    template <typename T>
    void Flags<T>::unset(T flag)
    {
        m_flags &= ~(1 << static_cast<unsigned long long>(flag));
    }

    template <typename T>
    bool Flags<T>::is_set(T flag) const
    {
        return m_flags & (1 << static_cast<unsigned long long>(flag));
    }
} // namespace qrawlr