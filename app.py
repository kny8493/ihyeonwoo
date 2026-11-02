"""
대학 정보 및 적성검사 시스템
"""
import streamlit as st
import pandas as pd
from utils import (
    load_data, get_response, create_visualization,
    save_chat_history, load_chat_history, get_popular_topics,
    summarize_chat, APTITUDE_QUESTIONS, analyze_aptitude
)

# 페이지 설정
st.set_page_config(
    page_title="대학 진로 상담 시스템",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 세션 상태 초기화
if 'mode' not in st.session_state:
    st.session_state.mode = None
if 'chat_messages' not in st.session_state:
    st.session_state.chat_messages = []
if 'aptitude_answers' not in st.session_state:
    st.session_state.aptitude_answers = []
if 'aptitude_current_q' not in st.session_state:
    st.session_state.aptitude_current_q = 0
if 'show_visualization' not in st.session_state:
    st.session_state.show_visualization = False
if 'last_vis_type' not in st.session_state:
    st.session_state.last_vis_type = None
if 'last_unknown_response' not in st.session_state:
    st.session_state.last_unknown_response = None

# 데이터 로드
@st.cache_data
def get_data():
    return load_data()

university_df, major_df, admission_df = get_data()

# 사이드바
with st.sidebar:
    st.title("📚 메뉴")
    
    # 홈으로 돌아가기 버튼
    if st.button("🏠 홈으로", use_container_width=True):
        st.session_state.mode = None
        st.session_state.aptitude_current_q = 0
        st.session_state.aptitude_answers = []
        st.session_state.chat_messages = []
        st.session_state.last_vis_type = None
        st.session_state.last_unknown_response = None
        st.rerun()
    
    st.markdown("---")
    
    # 인기 검색어
    st.subheader("🔥 주로 검색하는 것")
    popular_topics = get_popular_topics()
    
    if popular_topics:
        for i, (topic, count) in enumerate(popular_topics, 1):
            # 순위에 따른 이모지
            if i == 1:
                emoji = "🥇"
            elif i == 2:
                emoji = "🥈"
            elif i == 3:
                emoji = "🥉"
            else:
                emoji = "📌"
            st.markdown(f"{emoji} {i}. **{topic}** ({count}회)")
    else:
        st.info("아직 검색 기록이 없습니다.")
    
    st.markdown("---")
    
    # 대화 내역
    st.subheader("💬 예전 대화 내용")
    chat_history = load_chat_history()
    
    if chat_history:
        # 최근 5개만 표시
        for item in reversed(chat_history[-5:]):
            if 'summary' in item:
                st.markdown(f"- {item['summary']}")
    else:
        st.info("아직 대화 기록이 없습니다.")

# 메인 화면
if st.session_state.mode is None:
    # 홈 화면
    st.title("🎓 대학 진로 상담 시스템")
    st.markdown("### 환영합니다! 원하시는 서비스를 선택해주세요.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📊 대학 정보")
        st.markdown("""
        - 전국 주요 대학 정보
        - 학과별 상세 정보
        - 취업률 및 진학률 통계
        - AI 챗봇을 통한 상담
        """)
        if st.button("대학 정보 보기", use_container_width=True, type="primary"):
            st.session_state.mode = "university"
            st.rerun()
    
    with col2:
        st.markdown("### ✨ 적성검사")
        st.markdown("""
        - 나에게 맞는 진로 찾기
        - 10개의 질문으로 적성 분석
        - 추천 학과 및 진로 안내
        - 성향별 맞춤 정보 제공
        """)
        if st.button("적성검사 시작", use_container_width=True, type="primary"):
            st.session_state.mode = "aptitude"
            st.session_state.aptitude_current_q = 0
            st.session_state.aptitude_answers = []
            st.rerun()
    
    # 하단 통계 표시
    st.markdown("---")
    st.markdown("### 📈 최신 통계")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("전체 대학 수", f"{len(university_df)}개")
    with col2:
        st.metric("등록 학과 수", f"{len(major_df)}개")
    with col3:
        latest_rate = admission_df.iloc[-1]['대학진학률']
        st.metric("2023년 진학률", f"{latest_rate}%")
    with col4:
        avg_employment = major_df['취업률'].mean()
        st.metric("평균 취업률", f"{avg_employment:.1f}%")

elif st.session_state.mode == "university":
    # 대학 정보 챗봇 모드
    st.title("💬 대학 정보 상담 챗봇")
    st.markdown("궁금하신 대학이나 학과에 대해 질문해주세요!")
    
    # 채팅 메시지 표시
    chat_container = st.container()
    
    with chat_container:
        for message in st.session_state.chat_messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
                
                # 시각화가 있는 경우
                if "visualization" in message:
                    vis = message["visualization"]
                    if isinstance(vis, pd.DataFrame):
                        st.dataframe(vis, use_container_width=True)
                    elif vis is not None:
                        st.plotly_chart(vis, use_container_width=True)
                    else:
                        st.info("이 항목은 위 상담 내용으로 확인해주세요. 표시할 표나 그래프가 없습니다.")
    
    # 사용자 입력 처리
    # 시각화 대기 중인지 확인 (마지막 메시지가 시각화 제안인지 확인)
    waiting_for_vis = (st.session_state.last_vis_type is not None and 
                      len(st.session_state.chat_messages) > 0 and
                      st.session_state.chat_messages[-1].get("role") == "assistant" and
                      "표나 그래프를 보여줄까요?" in st.session_state.chat_messages[-1].get("content", ""))
    
    # 입력 프롬프트 설정
    if waiting_for_vis:
        input_prompt = "네 또는 아니요로 답변해주세요..."
    else:
        input_prompt = "질문을 입력하세요..."
    
    user_input = st.chat_input(input_prompt)
    
    if user_input:
        # 시각화 응답 처리
        if waiting_for_vis:
            vis_response_lower = user_input.lower().strip()
            
            # 긍정 응답 처리
            if any(word in vis_response_lower for word in ['네', '예', 'yes', '보여', '보여주', '좋아', 'ok', 'okay', '좋아요', '보고싶', '보고싶어', '보고 싶']):
                vis = create_visualization(
                    st.session_state.last_vis_type,
                    university_df, major_df, admission_df
                )
                
                st.session_state.chat_messages.append({
                    "role": "user",
                    "content": user_input
                })
                
                st.session_state.chat_messages.append({
                    "role": "assistant",
                    "content": "여기 표/그래프입니다:" if vis is not None else "이 항목은 위 상담 내용으로 확인해주세요.",
                    "visualization": vis
                })
                st.session_state.last_vis_type = None
                st.rerun()
            
            # 부정 응답 처리
            elif any(word in vis_response_lower for word in ['아니', 'no', '괜찮', '안', '필요없', '아니요', '괜찮아', '괜찮습니다', '싫', '싫어', '안 보고', '안 보']):
                st.session_state.chat_messages.append({
                    "role": "user",
                    "content": user_input
                })
                
                st.session_state.chat_messages.append({
                    "role": "assistant",
                    "content": "알겠습니다"
                })
                st.session_state.last_vis_type = None
                st.rerun()
            
            # 명확하지 않은 응답
            else:
                st.session_state.chat_messages.append({
                    "role": "user",
                    "content": user_input
                })
                
                st.session_state.chat_messages.append({
                    "role": "assistant",
                    "content": "표나 그래프를 보여드릴까요? '네' 또는 '아니요'로 답변해주세요."
                })
                st.rerun()
        
        # 일반 질문 처리
        else:
            # 모르는 질문 반복 방지: 같은 질문이 연속으로 들어온 경우 스킵
            if (st.session_state.last_unknown_response is not None and 
                st.session_state.last_unknown_response.lower().strip() == user_input.lower().strip()):
                # 같은 질문이면 응답하지 않고 무시
                st.rerun()
            
            # 사용자 메시지 추가
            st.session_state.chat_messages.append({
                "role": "user",
                "content": user_input
            })
            
            # 응답 생성
            response, can_visualize, vis_type = get_response(
                user_input, university_df, major_df, admission_df
            )
            
            # 모르는 질문인지 확인
            is_unknown = "죄송합니다" in response and "찾지 못하겠습니다" in response
            
            # 모르는 질문이면 기록해두고, 다음에 같은 질문이 오면 무시
            if is_unknown:
                st.session_state.last_unknown_response = user_input
            else:
                st.session_state.last_unknown_response = None
            
            # 챗봇 응답 추가 (한 번만)
            st.session_state.chat_messages.append({
                "role": "assistant",
                "content": response
            })
            
            # 시각화 제안 (모르는 질문이 아닌 경우만)
            if can_visualize and vis_type and not is_unknown:
                st.session_state.chat_messages.append({
                    "role": "assistant",
                    "content": "표나 그래프를 보여줄까요?"
                })
                st.session_state.last_vis_type = vis_type
            
            # 대화 기록 저장 (모르는 질문이 아닌 경우만)
            if not is_unknown:
                summary = summarize_chat(user_input, response)
                save_chat_history({
                    "question": user_input,
                    "response": response,
                    "summary": summary
                })
            
            st.rerun()
    
    # 예시 질문
    with st.expander("💡 예시 질문"):
        st.markdown("""
        **대학 정보**
        - 서울대학교에 대해 알려주세요
        - 연세대학교 정보 알려줘
        
        **학과 정보**
        - 컴퓨터공학과 취업률은 어떻게 되나요?
        - 의예과 정보를 알려주세요
        - 공학 계열 학과를 추천해주세요
        
        **진학률 정보**
        - 최근 대학 진학률은 어떤가요?
        
        **내신 기반 대학 추천** ⭐
        - 내신 2.5등급으로 갈 수 있는 대학 알려줘
        - 내신 3.0등급으로 성균관대학교 들어갈 수 있나요?
        - 내신 2.0등급으로 가능한 대학교는?
        - 내신 3.5등급으로 지원 가능한 인서울 대학 알려줘
        """)

elif st.session_state.mode == "aptitude":
    # 적성검사 모드
    st.title("✨ 적성검사")
    
    if st.session_state.aptitude_current_q < len(APTITUDE_QUESTIONS):
        # 질문 표시
        current_q = APTITUDE_QUESTIONS[st.session_state.aptitude_current_q]
        
        st.markdown(f"### 질문 {current_q['id']}/{len(APTITUDE_QUESTIONS)}")
        st.markdown(f"## {current_q['question']}")
        
        # 진행 바
        progress = st.session_state.aptitude_current_q / len(APTITUDE_QUESTIONS)
        st.progress(progress)
        
        st.markdown("---")
        
        # 선택지
        for key, option in current_q['options'].items():
            if st.button(f"{key}. {option}", use_container_width=True, key=f"option_{key}"):
                # 답변 저장
                st.session_state.aptitude_answers.append({
                    "question_id": current_q['id'],
                    "choice": key
                })
                st.session_state.aptitude_current_q += 1
                st.rerun()
    
    else:
        # 결과 표시
        st.markdown("## 🎉 적성검사 완료!")
        
        result = analyze_aptitude(st.session_state.aptitude_answers)
        
        st.success(f"당신의 성향은 **{result['primary_type']}** 입니다!")
        
        # 결과 상세
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown("### 📝 성향 설명")
            st.info(result['description'])
            
            st.markdown("### 🎓 추천 학과")
            for major_name in result['recommended_majors']:
                major_info = major_df[major_df['학과명'] == major_name]
                if not major_info.empty:
                    major_row = major_info.iloc[0]
                    with st.expander(f"**{major_name}**"):
                        st.markdown(f"- **분야**: {major_row['분야']}")
                        st.markdown(f"- **평균연봉**: {major_row['평균연봉']:,}만원")
                        st.markdown(f"- **취업률**: {major_row['취업률']}%")
                        st.markdown(f"- **필요역량**: {major_row['필요역량']}")
            
            st.markdown("### 💼 추천 직업")
            careers_text = ", ".join(result['recommended_careers'][:10])
            st.info(f"{careers_text}")
        
        with col2:
            st.markdown("### 📊 성향 분포")
            counts_df = pd.DataFrame(
                list(result['counts'].items()),
                columns=['성향', '점수']
            )
            st.bar_chart(counts_df.set_index('성향'))
        
        st.markdown("---")
        
        # 다시 하기 버튼
        if st.button("🔄 적성검사 다시 하기", use_container_width=True):
            st.session_state.aptitude_current_q = 0
            st.session_state.aptitude_answers = []
            st.rerun()
        
        # 대학 정보로 이동
        if st.button("📚 대학 정보 보러 가기", use_container_width=True, type="primary"):
            st.session_state.mode = "university"
            st.rerun()

# 푸터
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: gray;'>
    <p>🎓 대학 진로 상담 시스템 | Made with Streamlit</p>
</div>
""", unsafe_allow_html=True)

