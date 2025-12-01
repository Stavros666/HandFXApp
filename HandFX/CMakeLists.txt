cmake_minimum_required(VERSION 3.15)
project(HandFX VERSION 0.1)
add_subdirectory("../JUCE" JUCE_build)
juce_add_gui_app(HandFX
	COMPANY_NAME "StavrosParisis"
	PRODUCT_NAME "HandFX"
)


target_sources(HandFX PRIVATE
	Source/Main.cpp
	Source/MainComponent.cpp
	Source/AudioEngine.cpp
)
target_compile_features(HandFX PRIVATE cxx_std_17)

target_link_libraries(HandFX PRIVATE
juce::juce_gui_extra
juce::juce_audio_utils
juce::juce_dsp
juce::juce_osc
)