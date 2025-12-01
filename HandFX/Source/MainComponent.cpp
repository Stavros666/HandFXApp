#include "MainComponent.h"

MainComponent::MainComponent()
{
    addAndMakeVisible(helloButton);
    helloButton.setButtonText("Hello HandFX");
    helloButton.onClick = []{
        juce::AlertWindow::showMessageBoxAsync(
            juce::MessageBoxIconType::InfoIcon, "HandFX", "Welcome to HandFX!");
    };
    setSize(800, 600);
}

void MainComponent::resized()
{
    helloButton.setBounds(getLocalBounds().reduced(20));
}

